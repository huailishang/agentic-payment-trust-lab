"""Explicit local order-only recovery. No payment, HTTP, or import-time execution.

The approval write lock stays held across the native transaction's commit. Only
the merchant transaction database stores the authoritative consumption result;
there is no second approval-ledger consumption commit to reconcile after a crash.
"""
import asyncio
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3

from APPROVAL_INBOX import ApprovalDenied, ApprovalInbox, _canonical, _digest, _fields, _text
import db
from exceptions import UcpError
from services.checkout_service import CheckoutService
from services.fulfillment_service import FulfillmentService
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


def _denied(reason):
    return {"status": "DENIED", "reason": reason}


def _binding(box, row, request):
    if row is None:
        raise ApprovalDenied("APPROVAL_NOT_FOUND")
    record = json.loads(row["record_json"])
    for key in ("approval_id", "checkout_id", "payment_ref"):
        if row[key] != record[key] or record[key] != request[key]:
            raise ApprovalDenied("APPROVAL_BINDING_MISMATCH")
    operator, policy, context_digest = box._trusted()
    if (record["operator_id"] != operator or row["operator_id"] != operator
            or record["policy_version"] != policy
            or record["context_digest"] != context_digest):
        raise ApprovalDenied("OPERATOR_CONTEXT_MISMATCH")
    if record["disposition"] != "ORDER_COMPLETION":
        raise ApprovalDenied("UNSUPPORTED_DISPOSITION")
    return record


async def _recover(config, request, box, ledger, record, hook):
    # URI modes prevent accidental creation of missing input databases. The
    # product engine is read-only; only the actual native transaction may write.
    products_engine = create_async_engine(URL.create(
        "sqlite+aiosqlite", database=Path(config["products_path"]).resolve().as_uri(),
        query={"mode": "ro", "uri": "true"}), connect_args={"timeout": 0})
    transactions_engine = create_async_engine(URL.create(
        "sqlite+aiosqlite", database=box.tx.as_uri(),
        query={"mode": "rw", "uri": "true"}), connect_args={"timeout": 0})
    try:
        async with AsyncSession(products_engine, expire_on_commit=False) as products:
            async with AsyncSession(transactions_engine, expire_on_commit=False) as transactions:
                try:
                    connection = await transactions.connection()
                    await connection.exec_driver_sql("BEGIN IMMEDIATE")
                    await db.ensure_recovery_consumptions(transactions)
                    tables = {}
                    for table in ("checkouts", "h50_attempts", "h53_authorizations",
                                  "h50_confirmations", "inventory", "orders", "h62_consumptions"):
                        result = await transactions.execute(text(
                            'SELECT * FROM "' + table + '" ORDER BY rowid'))
                        tables[table] = [dict(row) for row in result.mappings()]

                    # Replay is a result read, not a new execution authorization.
                    # Check exact owner/config/transaction binding before this path.
                    consumed = box._consumption(record, transaction_rows=tables)
                    if consumed:
                        response = json.loads(consumed["response_json"])
                        await transactions.rollback()
                        return dict(response, status="REPLAY")

                    if (row := ledger.execute(
                            "SELECT revoke_request_json FROM approvals WHERE approval_id=?",
                            (record["approval_id"],)).fetchone()) is None:
                        raise ApprovalDenied("APPROVAL_NOT_FOUND")
                    if row["revoke_request_json"] or ledger.execute(
                            "SELECT 1 FROM approval_events WHERE approval_id=? AND kind='REVOKED'",
                            (record["approval_id"],)).fetchone():
                        raise ApprovalDenied("APPROVAL_REVOKED")
                    if box._clock() >= record["expires_at"]:
                        raise ApprovalDenied("APPROVAL_EXPIRED")
                    source = box._source(request["checkout_id"], transaction_rows=tables)
                    if not box._eligible(source, request["checkout_id"], request["payment_ref"]):
                        raise ApprovalDenied("SOURCE_NOT_ELIGIBLE")
                    if _digest(source) != record["source_digest"]:
                        raise ApprovalDenied("APPROVAL_STALE_SOURCE")

                    service = CheckoutService(FulfillmentService(), products, transactions,
                                              config["base_url"])
                    checkout = await service._get_and_validate_checkout(request["checkout_id"])
                    service._ensure_modifiable(checkout, "recover")
                    identity = {key: request[key] for key in (
                        "approval_id", "checkout_id", "payment_ref")}
                    request_hash = service._compute_hash(
                        "approved_order_recovery", identity, resource_id=request["checkout_id"])
                    key = "h62-recovery:" + request["request_key"]
                    existing = await db.get_idempotency_record(transactions, key)
                    if existing is not None:
                        # A valid prior recovery always has its atomic receipt.
                        raise ApprovalDenied("RECOVERY_IDEMPOTENCY_CONFLICT")
                    checkout = await service.prepare_order(
                        checkout, key, request_hash, require_products=True)
                    response = {
                        "status": "RECOVERED", "order_id": checkout.order.id,
                        "notification_status": "PENDING_NOT_SENT",
                        "checkout": checkout.model_dump(mode="json", by_alias=True, exclude_none=True),
                    }
                    await db.save_recovery_consumption(transactions, {
                        **{key: record[key] for key in (
                            "approval_id", "checkout_id", "payment_ref",
                            "source_digest", "context_digest")},
                        "order_id": checkout.order.id, "response_json": _canonical(response),
                    })
                    # Hook observes the actual order/stock/receipt transaction.
                    hook("before_commit")
                    await transactions.commit()
                    hook("after_commit")
                    return response
                except BaseException:
                    await transactions.rollback()
                    raise
    finally:
        await products_engine.dispose()
        await transactions_engine.dispose()


def run(config, request, *, hook):
    """Consume one new local approval, or read its previously committed result."""
    try:
        # A synchronous public entry point must never block an existing server loop.
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            return _denied("EXISTING_EVENT_LOOP_UNSUPPORTED")
        _fields(request, ("approval_id", "checkout_id", "payment_ref", "request_key"))
        if not all(_text(request[key]) for key in request):
            return _denied("INVALID_RECOVERY_REQUEST")
        if not isinstance(config, dict) or type(config.get("now")) is not int:
            return _denied("INVALID_TRUSTED_CONFIGURATION")
        paths = [Path(config[key]).resolve() for key in (
            "transactions_path", "products_path", "psp_path", "ledger_path")]
        if not all(path.is_file() for path in paths):
            return _denied("SOURCE_UNAVAILABLE")
        if any(os.path.samefile(left, right) for i, left in enumerate(paths)
               for right in paths[i + 1:]):
            return _denied("SOURCE_LEDGER_NOT_ISOLATED")
        box = ApprovalInbox(
            transactions_path=config["transactions_path"], psp_path=config["psp_path"],
            ledger_path=config["ledger_path"], operator_context=config["operator_context"],
            now=lambda: config["now"])
        with closing(box._ledger_connection()) as ledger:
            ledger.execute("BEGIN IMMEDIATE")
            hook("approval_locked")
            row = ledger.execute("SELECT * FROM approvals WHERE approval_id=?",
                                 (request["approval_id"],)).fetchone()
            record = _binding(box, row, request)
            # No approval write follows the native transaction commit. Closing
            # the unchanged ledger transaction releases its serialization lock.
            return asyncio.run(_recover(config, request, box, ledger, record, hook))
    except ApprovalDenied as exc:
        return _denied(exc.code)
    except UcpError as exc:
        return _denied(exc.code)
    except (sqlite3.Error, SQLAlchemyError) as exc:
        detail = str(exc).lower()
        return _denied("RECOVERY_BUSY" if "locked" in detail or "busy" in detail
                       else "RECOVERY_STORAGE_ERROR")
    except (OSError, ValueError, TypeError, KeyError):
        return _denied("INVALID_RECOVERY_INPUT")
