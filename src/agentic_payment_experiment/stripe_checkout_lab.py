"""H68 single-resource merchant state. Private SQLite is authoritative for local joins.

No Stripe payment is performed here. A caller must supply native Stripe GET
observations only after the existing runtime gate; webhooks alone never mark
a payment paid or trigger fulfillment. Client-delivered bytes must be observed.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Any

from .adapters.stripe_checkout import StripeCheckoutError, verify_webhook
from .models import (
    PaymentExecutionRecord, PaymentStatus, PaymentStatusObservation,
)
from .payment_recovery import assess_payment_recovery

CASES = {"N01", "C01", "R01", "D01"}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class StripeLabLedger:
    """SQLite prevents session replacement, cross-operation reuse and double delivery."""

    def __init__(self, database: str | Path):
        self.database = str(database)
        path = Path(self.database)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._open() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS operations(
                operation_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL, case_id TEXT NOT NULL UNIQUE,
                order_id TEXT NOT NULL UNIQUE, request_id TEXT NOT NULL UNIQUE,
                payment_id TEXT NOT NULL UNIQUE,
                session_id TEXT UNIQUE,
                resource_sha256 TEXT NOT NULL,
                amount_minor INTEGER NOT NULL CHECK(amount_minor = 100),
                currency TEXT NOT NULL CHECK(currency = 'usd'),
                state TEXT NOT NULL DEFAULT 'CREATED',
                intent_id TEXT, charge_id TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS webhook_receipts(
                event_id TEXT PRIMARY KEY,
                operation_id TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                received_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS delivery_attempts(
                attempt_id TEXT PRIMARY KEY,
                operation_id TEXT NOT NULL,
                state TEXT NOT NULL,
                receipt_ref TEXT UNIQUE,
                actual_sha256 TEXT,
                at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_successful_delivery
                ON delivery_attempts(operation_id) WHERE state = 'SUCCEEDED';
            CREATE TABLE IF NOT EXISTS recoveries(
                operation_id TEXT PRIMARY KEY,
                initial_status TEXT NOT NULL,
                observed_status TEXT NOT NULL,
                recovery_status TEXT NOT NULL,
                retry_allowed INTEGER NOT NULL,
                at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS authority_contexts(
                operation_id TEXT PRIMARY KEY REFERENCES operations(operation_id),
                snapshot_sha256 TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL
            );
            """)

    @contextmanager
    def _open(self):
        """Open one real connection and always close it, including failed writes.

        sqlite3's default connection context manager commits/rolls back but does
        not close the handle, which leaves Windows temporary databases locked.
        """
        con = sqlite3.connect(self.database, timeout=10)
        try:
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA busy_timeout = 10000")
            con.execute("PRAGMA foreign_keys = ON")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def register(self, *, operation_id: str, run_id: str, case_id: str,
                 order_id: str, request_id: str, payment_id: str,
                 resource_sha256: str) -> None:
        if case_id not in CASES or not all(
            isinstance(x, str) and x.strip()
            for x in (operation_id, run_id, order_id, request_id, payment_id)
        ):
            raise StripeCheckoutError("operation_identity_invalid")
        if len(resource_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in resource_sha256
        ):
            raise StripeCheckoutError("resource_digest_invalid")
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute(
                "SELECT * FROM operations WHERE operation_id = ?", (operation_id,)
            ).fetchone()
            if existing:
                if not (
                    existing["run_id"] == run_id and existing["case_id"] == case_id
                    and existing["order_id"] == order_id
                    and existing["request_id"] == request_id
                    and existing["payment_id"] == payment_id
                    and existing["resource_sha256"] == resource_sha256
                ):
                    raise StripeCheckoutError("operation_identity_mutation")
                return
            try:
                con.execute(
                    """INSERT INTO operations
                       (operation_id,run_id,case_id,order_id,request_id,payment_id,
                        resource_sha256,amount_minor,currency,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,100,'usd',?,?)""",
                    (operation_id, run_id, case_id, order_id, request_id,
                     payment_id, resource_sha256, self._now(), self._now()),
                )
            except sqlite3.IntegrityError:
                raise StripeCheckoutError("duplicate_business_operation") from None

    def get(self, operation_id: str) -> dict[str, Any]:
        with self._open() as con:
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id = ?", (operation_id,)
            ).fetchone()
        if row is None:
            raise StripeCheckoutError("unknown_business_operation")
        return dict(row)

    @staticmethod
    def _authority_business_binding(ctx, row) -> None:
        """A loaded graph belongs to exactly the original registered operation."""
        c = ctx.confirmation_record
        if (
            ctx.order.order_id != row["order_id"]
            or ctx.request.request_id != row["request_id"]
            or ctx.request.order_ref != row["order_id"]
            or ctx.execution.payment_id != row["payment_id"]
            or ctx.execution.order_id != row["order_id"]
            or ctx.execution.request_id != row["request_id"]
            or ctx.order.currency != row["currency"]
            or ctx.request.currency != row["currency"]
            or ctx.execution.currency != row["currency"]
            or ctx.request.amount != ctx.order.total_amount
            or ctx.execution.amount != ctx.order.total_amount
            or ctx.request.payee != ctx.order.payee
            or ctx.execution.payee != ctx.order.payee
            or c is None
            or c.authorized_order_id != ctx.order.order_id
            or c.authorized_order_version != ctx.order.order_version
            or c.authority_id != ctx.mandate.mandate_id
            or c.authority_version != ctx.mandate.authority_version
        ):
            raise StripeCheckoutError("authority_original_business_binding_invalid")

    def record_authority(self, operation_id, ctx, *, resource_sha256, recorded_at) -> str:
        """Atomically freeze the original context before any payment callback."""
        from .adapters.stripe_checkout import GateContext, _validate_operation
        from .models import Decision
        from .stripe_authority_context import (
            _decode, deserialize_authority, serialize_authority,
        )
        if not isinstance(ctx, GateContext) or not isinstance(recorded_at, datetime) or (
            recorded_at.tzinfo is None or recorded_at.utcoffset() is None
        ):
            raise StripeCheckoutError("authority_record_input_invalid")
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is None:
                raise StripeCheckoutError("unknown_business_operation")
            if resource_sha256 != row["resource_sha256"]:
                raise StripeCheckoutError("authority_operation_resource_invalid")
            self._authority_business_binding(ctx, row)
            if _validate_operation(ctx, resource_sha256, recorded_at) is not Decision.ALLOW:
                raise StripeCheckoutError("authority_original_gate_not_allowed")
            payload, digest = serialize_authority(
                operation_id, ctx, resource_sha256=resource_sha256,
                recorded_at=recorded_at, run_id=row["run_id"],
            )
            existing = con.execute(
                "SELECT snapshot_sha256,payload_json FROM authority_contexts WHERE operation_id=?",
                (operation_id,),
            ).fetchone()
            if existing is not None:
                first_payload = existing["payload_json"]
                first_digest = existing["snapshot_sha256"]
                if _sha(first_payload.encode("utf-8")) != first_digest:
                    raise StripeCheckoutError("authority_snapshot_digest_mismatch")
                # Validate the stored original before using its immutable recorded_at.
                deserialize_authority(
                    first_payload, operation_id=operation_id,
                    resource_sha256=resource_sha256, run_id=row["run_id"],
                )
                first_recorded_at = _decode(json.loads(first_payload)["recorded_at"])
                original_payload, original_digest = serialize_authority(
                    operation_id, ctx, resource_sha256=resource_sha256,
                    recorded_at=first_recorded_at, run_id=row["run_id"],
                )
                if original_payload != first_payload or original_digest != first_digest:
                    raise StripeCheckoutError("authority_original_fact_immutable")
                return first_digest
            if row["state"] != "CREATED":
                raise StripeCheckoutError("authority_original_must_precede_session")
            con.execute(
                "INSERT INTO authority_contexts(operation_id,snapshot_sha256,payload_json) VALUES(?,?,?)",
                (operation_id, digest, payload),
            )
            return digest

    def load_authority(self, operation_id, *, expected_sha256):
        """Load exactly the original graph, without refreshing its clock."""
        from .stripe_authority_context import deserialize_authority
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in expected_sha256
        ):
            raise StripeCheckoutError("authority_reference_invalid")
        with self._open() as con:
            con.execute("BEGIN")
            operation = con.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            original = con.execute(
                "SELECT * FROM authority_contexts WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if operation is None or original is None:
                raise StripeCheckoutError("authority_original_snapshot_missing")
            if original["snapshot_sha256"] != expected_sha256 or (
                _sha(original["payload_json"].encode("utf-8")) != expected_sha256
            ):
                raise StripeCheckoutError("authority_snapshot_digest_mismatch")
            context = deserialize_authority(
                original["payload_json"], operation_id=operation_id,
                resource_sha256=operation["resource_sha256"],
                run_id=operation["run_id"],
            )
            self._authority_business_binding(context, operation)
            return context

    def bind_session(self, operation_id: str, session: dict) -> None:
        """Session is established by one already-approved create callback."""
        if not str(session.get("id", "")).startswith("cs_test_"):
            raise StripeCheckoutError("non_test_session")
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id = ?", (operation_id,)
            ).fetchone()
            if row is None:
                raise StripeCheckoutError("unknown_business_operation")
            if (
                session.get("livemode") is not False
                or session.get("mode") != "payment"
                or session.get("currency") != "usd"
                or type(session.get("amount_total")) is not int
                or session["amount_total"] != 100
                or session.get("client_reference_id") != row["order_id"]
                or session.get("metadata", {}).get("h68_run_id") != row["run_id"]
                or session.get("metadata", {}).get("h68_operation_id") != row["operation_id"]
                or session.get("metadata", {}).get("h68_resource_sha256") != row["resource_sha256"]
            ):
                raise StripeCheckoutError("session_operation_binding_invalid")
            if row["session_id"] is not None and row["session_id"] != session["id"]:
                raise StripeCheckoutError("second_session_for_same_operation")
            if row["state"] not in {"CREATED", "SESSION_OPEN"}:
                raise StripeCheckoutError("session_rebind_after_payment")
            try:
                con.execute(
                    "UPDATE operations SET session_id=?,state='SESSION_OPEN',updated_at=? WHERE operation_id=?",
                    (session["id"], self._now(), operation_id),
                )
            except sqlite3.IntegrityError:
                raise StripeCheckoutError("session_belongs_to_other_operation") from None

    def mark_unknown(self, operation_id: str) -> None:
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is None or not row["session_id"] or row["state"] not in {"SESSION_OPEN", "UNKNOWN"}:
                raise StripeCheckoutError("unknown_transition_invalid")
            con.execute("UPDATE operations SET state='UNKNOWN',updated_at=? WHERE operation_id=?",
                        (self._now(), operation_id))

    def observe(self, operation_id: str, session: dict,
                intent: dict | None, charge: dict | None) -> str:
        """Only an original-session independent provider query may update paid state."""
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is None or session.get("id") != row["session_id"]:
                raise StripeCheckoutError("provider_observation_wrong_session")
            if (
                session.get("livemode") is not False
                or session.get("currency") != "usd"
                or type(session.get("amount_total")) is not int
                or session["amount_total"] != 100
                or session.get("client_reference_id") != row["order_id"]
            ):
                raise StripeCheckoutError("provider_observation_amount_or_origin")
            if session.get("status") == "expired" and session.get("payment_status") == "unpaid":
                if charge is not None or row["state"] == "PAID_CONFIRMED":
                    raise StripeCheckoutError("cancel_charge_conflict")
                state = "CANCELLED"
                intent_id = intent["id"] if isinstance(intent, dict) else None
                charge_id = None
            elif session.get("status") == "complete" and session.get("payment_status") == "paid":
                if not (isinstance(intent, dict) and isinstance(charge, dict)):
                    raise StripeCheckoutError("paid_native_objects_missing")
                if (
                    session.get("payment_intent") != intent.get("id")
                    or intent.get("latest_charge") != charge.get("id")
                    or charge.get("payment_intent") != intent.get("id")
                    or intent.get("livemode") is not False
                    or charge.get("livemode") is not False
                    or intent.get("status") != "succeeded"
                    or charge.get("status") != "succeeded"
                    or charge.get("paid") is not True
                    or charge.get("captured") is not True
                    or any(type(obj.get("amount")) is not int or obj["amount"] != 100
                           or obj.get("currency") != "usd" for obj in (intent,charge))
                ):
                    raise StripeCheckoutError("provider_payment_chain_invalid")
                if row["state"] == "CANCELLED":
                    raise StripeCheckoutError("cancel_paid_conflict")
                if row["intent_id"] and row["intent_id"] != intent["id"]:
                    raise StripeCheckoutError("changed_intent_for_operation")
                if row["charge_id"] and row["charge_id"] != charge["id"]:
                    raise StripeCheckoutError("changed_charge_for_operation")
                state, intent_id, charge_id = "PAID_CONFIRMED", intent["id"], charge["id"]
            else:
                raise StripeCheckoutError("provider_status_inconclusive")
            con.execute(
                "UPDATE operations SET state=?,intent_id=?,charge_id=?,updated_at=? WHERE operation_id=?",
                (state, intent_id, charge_id, self._now(), operation_id),
            )
            return state

    def ingest_webhook(self, *, operation_id: str, body: bytes, signature: str,
                       test_secret: str, received_at: datetime) -> bool:
        event = verify_webhook(body, signature, test_secret, received_at)
        ref = event.get("data", {}).get("object", {}).get("id")
        row = self.get(operation_id)
        event_type = event.get("type", "")
        if event_type.startswith("checkout.session."):
            if ref != row["session_id"]:
                raise StripeCheckoutError("webhook_cross_session")
        elif event_type == "payment_intent.succeeded":
            # A valid HMAC alone cannot attach an arbitrary intent to our order.
            # The binding must already be proven by an original-session query.
            if (not row["intent_id"] or row["intent_id"] != ref
                    or row["state"] != "PAID_CONFIRMED"):
                raise StripeCheckoutError("webhook_intent_not_bound_to_session")
        else:
            raise StripeCheckoutError("webhook_event_type_not_supported")
        event_id = str(event.get("id", ""))
        if not event_id.startswith("evt_"):
            raise StripeCheckoutError("webhook_event_id_invalid")
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute(
                "SELECT * FROM webhook_receipts WHERE event_id=?", (event_id,)
            ).fetchone()
            if existing is not None:
                if existing["operation_id"] != operation_id or existing["payload_sha256"] != _sha(body):
                    raise StripeCheckoutError("webhook_event_id_collision")
                return False
            con.execute(
                "INSERT INTO webhook_receipts VALUES (?,?,?,?)",
                (event_id, operation_id, _sha(body), received_at.isoformat()),
            )
        return True

    def recover_original(self, operation_id: str, payment: PaymentExecutionRecord,
                         observation: PaymentStatusObservation):
        row = self.get(operation_id)
        if (
            not row["session_id"]
            or payment.payment_id != row["payment_id"]
            or payment.request_id != row["request_id"]
            or payment.order_id != row["order_id"]
            or payment.provider_ref != row["session_id"]
        ):
            raise StripeCheckoutError("recovery_original_payment_mismatch")
        if (
            observation.payment_id != payment.payment_id
            or observation.order_id != row["order_id"]
            or observation.provider_ref != row["session_id"]
        ):
            raise StripeCheckoutError("recovery_observation_mismatch")
        outcome = assess_payment_recovery(payment, observation, known_attempts=(payment,))
        with self._open() as con:
            con.execute(
                "INSERT OR REPLACE INTO recoveries VALUES (?,?,?,?,?,?)",
                (operation_id, payment.status.value, observation.status.value,
                 outcome.recovery_status.value, int(outcome.retry_allowed), self._now()),
            )
        # An UNKNOWN case is never allowed to create a second payment from this operation.
        return outcome

    def record_client_delivery(self, operation_id: str, received: bytes,
                               *, inject_failure: bool = False) -> str | None:
        """Must be called only with bytes actually observed by the client."""
        if not isinstance(received, bytes):
            raise StripeCheckoutError("delivery_client_bytes_required")
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is None or row["state"] != "PAID_CONFIRMED":
                raise StripeCheckoutError("unpaid_order_cannot_deliver")
            success = con.execute(
                "SELECT receipt_ref FROM delivery_attempts WHERE operation_id=? AND state='SUCCEEDED'",
                (operation_id,),
            ).fetchone()
            if success is not None:
                return success["receipt_ref"]
            now = self._now()
            if inject_failure:
                con.execute(
                    "INSERT INTO delivery_attempts VALUES (?,?,?,NULL,NULL,?)",
                    ("failure-" + uuid4().hex, operation_id, "FAILED", now),
                )
                return None
            if _sha(received) != row["resource_sha256"]:
                raise StripeCheckoutError("client_content_hash_mismatch")
            receipt = "delivery-" + uuid4().hex
            con.execute(
                "INSERT INTO delivery_attempts VALUES (?,?,?,?,?,?)",
                ("attempt-" + uuid4().hex, operation_id, "SUCCEEDED",
                 receipt, _sha(received), now),
            )
            return receipt

    def delivery_history(self, operation_id: str) -> list[dict]:
        with self._open() as con:
            rows = con.execute(
                "SELECT state,receipt_ref,actual_sha256,at FROM delivery_attempts WHERE operation_id=? ORDER BY rowid",
                (operation_id,),
            ).fetchall()
            return [dict(row) for row in rows]
