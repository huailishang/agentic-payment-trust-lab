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
            CREATE TABLE IF NOT EXISTS confirmation_withdrawals(
                operation_id TEXT PRIMARY KEY REFERENCES authority_contexts(operation_id),
                snapshot_sha256 TEXT NOT NULL,
                confirmation_id TEXT NOT NULL,
                subject_ref TEXT NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                received_at TEXT NOT NULL,
                source TEXT NOT NULL CHECK(source = 'LOCAL_USER_CONTROL')
            );
            CREATE TABLE IF NOT EXISTS mandate_shutdowns(
                subject_ref TEXT NOT NULL,
                mandate_id TEXT NOT NULL,
                authority_version TEXT NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                anchor_operation_id TEXT NOT NULL REFERENCES authority_contexts(operation_id),
                anchor_snapshot_sha256 TEXT NOT NULL,
                received_at TEXT NOT NULL,
                source TEXT NOT NULL CHECK(source = 'LOCAL_USER_CONTROL'),
                PRIMARY KEY(subject_ref, mandate_id, authority_version)
            );
            CREATE TABLE IF NOT EXISTS stored_action_control_events(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK(kind IN ('STOP_ACCEPTED','ADMITTED','DENIED','OUTCOME','RECOVERY_OBSERVED')),
                operation_id TEXT NOT NULL REFERENCES authority_contexts(operation_id),
                action TEXT,
                snapshot_sha256 TEXT NOT NULL,
                admission_ref TEXT,
                stop_event_ref TEXT,
                payload_json TEXT NOT NULL,
                fact_sha256 TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_stored_admission
                ON stored_action_control_events(operation_id, action) WHERE kind='ADMITTED';
            CREATE UNIQUE INDEX IF NOT EXISTS one_stored_admission_ref
                ON stored_action_control_events(admission_ref) WHERE kind='ADMITTED';
            CREATE UNIQUE INDEX IF NOT EXISTS one_stored_outcome
                ON stored_action_control_events(admission_ref) WHERE kind='OUTCOME';
            CREATE UNIQUE INDEX IF NOT EXISTS one_stored_stop
                ON stored_action_control_events(stop_event_ref) WHERE kind='STOP_ACCEPTED';
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

    def _load_authority_in_transaction(self, con, operation_id, expected_sha256):
        from .stripe_authority_context import _decode, deserialize_authority
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in expected_sha256
        ):
            raise StripeCheckoutError("authority_reference_invalid")
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
        recorded_at = _decode(json.loads(original["payload_json"])["recorded_at"])
        return context, recorded_at

    def load_authority(self, operation_id, *, expected_sha256):
        """Load exactly the original graph, without refreshing its clock."""
        with self._open() as con:
            con.execute("BEGIN")
            context, _ = self._load_authority_in_transaction(
                con, operation_id, expected_sha256
            )
            return context

    @staticmethod
    def _withdrawal_fact(operation_id, expected_sha256, context, recorded_at, *,
                         confirmation_id, subject_ref, event_id, received_at):
        from .trusted_execution.confirmation import ConfirmationStatus
        confirmation = context.confirmation_record
        if (
            confirmation is None
            or confirmation.status is not ConfirmationStatus.CONFIRMED
            or not all(isinstance(value, str) and value.strip() for value in
                       (operation_id, confirmation_id, subject_ref, event_id))
            or confirmation_id != confirmation.confirmation_id
            or subject_ref != context.mandate.user_id
        ):
            raise StripeCheckoutError("confirmation_withdrawal_binding_invalid")
        if (
            not isinstance(received_at, datetime)
            or received_at.tzinfo is None
            or received_at.utcoffset() is None
            or received_at < recorded_at
            or received_at < confirmation.confirmed_at
        ):
            raise StripeCheckoutError("confirmation_withdrawal_time_invalid")
        return {
            "event_id": event_id,
            "operation_id": operation_id,
            "snapshot_sha256": expected_sha256,
            "confirmation_id": confirmation_id,
            "subject_ref": subject_ref,
            "received_at": received_at.astimezone(timezone.utc).isoformat(),
            "source": "LOCAL_USER_CONTROL",
        }

    def _read_withdrawal(self, con, operation_id, expected_sha256, context, recorded_at):
        row = con.execute(
            "SELECT * FROM confirmation_withdrawals WHERE operation_id=?",
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            fact = self._withdrawal_fact(
                operation_id, expected_sha256, context, recorded_at,
                confirmation_id=row["confirmation_id"], subject_ref=row["subject_ref"],
                event_id=row["event_id"], received_at=datetime.fromisoformat(row["received_at"]),
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise StripeCheckoutError("confirmation_withdrawal_state_invalid") from error
        if dict(row) != fact:
            raise StripeCheckoutError("confirmation_withdrawal_state_invalid")
        return fact

    def record_confirmation_withdrawal(self, operation_id, *, expected_sha256,
                                       confirmation_id, subject_ref, event_id, received_at):
        """Trusted local user-control boundary only; subject authentication is upstream."""
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            context, recorded_at = self._load_authority_in_transaction(
                con, operation_id, expected_sha256
            )
            fact = self._withdrawal_fact(
                operation_id, expected_sha256, context, recorded_at,
                confirmation_id=confirmation_id, subject_ref=subject_ref,
                event_id=event_id, received_at=received_at,
            )
            existing = self._read_withdrawal(
                con, operation_id, expected_sha256, context, recorded_at
            )
            if existing is not None:
                if existing != fact:
                    raise StripeCheckoutError("confirmation_withdrawal_conflict")
                return existing
            try:
                con.execute(
                    """INSERT INTO confirmation_withdrawals
                       (operation_id,snapshot_sha256,confirmation_id,subject_ref,event_id,received_at,source)
                       VALUES (:operation_id,:snapshot_sha256,:confirmation_id,:subject_ref,:event_id,:received_at,:source)""",
                    fact,
                )
            except sqlite3.IntegrityError:
                raise StripeCheckoutError("confirmation_withdrawal_conflict") from None
            return fact

    def get_confirmation_withdrawal(self, operation_id, *, expected_sha256):
        """Return only a verified, bound withdrawal fact; unreadable state is an error."""
        with self._open() as con:
            con.execute("BEGIN")
            context, recorded_at = self._load_authority_in_transaction(
                con, operation_id, expected_sha256
            )
            return self._read_withdrawal(
                con, operation_id, expected_sha256, context, recorded_at
            )

    @staticmethod
    def _mandate_key(context):
        mandate = context.mandate
        key = (mandate.user_id, mandate.mandate_id, mandate.authority_version)
        if not all(isinstance(value, str) and value.strip() for value in key):
            raise StripeCheckoutError("mandate_shutdown_binding_invalid")
        return key

    def _mandate_shutdown_fact(self, anchor_operation_id, expected_sha256,
                               context, recorded_at, *, subject_ref, mandate_id,
                               authority_version, event_id, received_at):
        key = self._mandate_key(context)
        confirmation = context.confirmation_record
        if (
            not all(isinstance(value, str) and value.strip() for value in
                    (anchor_operation_id, subject_ref, mandate_id, authority_version, event_id))
            or key != (subject_ref, mandate_id, authority_version)
            or confirmation is None
        ):
            raise StripeCheckoutError("mandate_shutdown_binding_invalid")
        if (
            not isinstance(received_at, datetime)
            or received_at.tzinfo is None
            or received_at.utcoffset() is None
            or received_at < recorded_at
            or received_at < confirmation.confirmed_at
        ):
            raise StripeCheckoutError("mandate_shutdown_time_invalid")
        return {
            "event_id": event_id,
            "subject_ref": subject_ref,
            "mandate_id": mandate_id,
            "authority_version": authority_version,
            "anchor_operation_id": anchor_operation_id,
            "anchor_snapshot_sha256": expected_sha256,
            "received_at": received_at.astimezone(timezone.utc).isoformat(),
            "source": "LOCAL_USER_CONTROL",
        }

    def _read_mandate_shutdown(self, con, key):
        row = con.execute(
            """SELECT * FROM mandate_shutdowns
               WHERE subject_ref=? AND mandate_id=? AND authority_version=?""",
            key,
        ).fetchone()
        if row is None:
            return None
        try:
            anchor, recorded_at = self._load_authority_in_transaction(
                con, row["anchor_operation_id"], row["anchor_snapshot_sha256"]
            )
            fact = self._mandate_shutdown_fact(
                row["anchor_operation_id"], row["anchor_snapshot_sha256"], anchor,
                recorded_at, subject_ref=row["subject_ref"], mandate_id=row["mandate_id"],
                authority_version=row["authority_version"], event_id=row["event_id"],
                received_at=datetime.fromisoformat(row["received_at"]),
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise StripeCheckoutError("mandate_shutdown_state_invalid") from error
        if dict(row) != fact or self._mandate_key(anchor) != key:
            raise StripeCheckoutError("mandate_shutdown_state_invalid")
        return fact

    @staticmethod
    def _control_json(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    def _append_control(self, con, *, kind, operation_id, snapshot_sha256,
                        action=None, admission_ref=None, stop_event_ref=None, details=None):
        sequence = con.execute(
            "SELECT COALESCE(MAX(sequence), 0)+1 FROM stored_action_control_events"
        ).fetchone()[0]
        event = dict(sequence=sequence, kind=kind, operation_id=operation_id,
                     snapshot_sha256=snapshot_sha256, action=action,
                     admission_ref=admission_ref, stop_event_ref=stop_event_ref,
                     details=details or {})
        payload = self._control_json(event)
        con.execute(
            """INSERT INTO stored_action_control_events
               (sequence,kind,operation_id,snapshot_sha256,action,admission_ref,stop_event_ref,payload_json,fact_sha256)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (sequence, kind, operation_id, snapshot_sha256, action, admission_ref,
             stop_event_ref, payload, _sha(payload.encode("utf-8"))),
        )
        return event

    def _control_history(self, con):
        """Validate immutable local facts and native references in a single snapshot."""
        events, keys, admissions, outcomes, stops = [], {}, {}, {}, {}
        for row in con.execute("SELECT * FROM stored_action_control_events ORDER BY sequence"):
            try:
                event = json.loads(row["payload_json"])
                fields = ("sequence", "kind", "operation_id", "snapshot_sha256", "action",
                          "admission_ref", "stop_event_ref")
                if (not isinstance(event, dict) or set(event) != set(fields) | {"details"}
                    or not isinstance(event["details"], dict)
                    or any(event[k] != row[k] for k in fields)
                    or self._control_json(event) != row["payload_json"]
                    or _sha(row["payload_json"].encode("utf-8")) != row["fact_sha256"]
                    or type(event["sequence"]) is not int or event["sequence"] <= 0):
                    raise ValueError("control_fact_mismatch")
                op, digest = event["operation_id"], event["snapshot_sha256"]
                if (op, digest) not in keys:
                    ctx, _ = self._load_authority_in_transaction(con, op, digest)
                    keys[(op, digest)] = self._mandate_key(ctx)
                key = keys[(op, digest)]
                kind, action, ref, stop = (event[k] for k in
                    ("kind", "action", "admission_ref", "stop_event_ref"))
                details = event["details"]
                if kind == "STOP_ACCEPTED":
                    native = self._read_mandate_shutdown(con, key)
                    if (not native or native != details.get("receipt") or stop != native["event_id"]
                        or op != native["anchor_operation_id"] or digest != native["anchor_snapshot_sha256"]
                        or action is not None or ref is not None or key in stops):
                        raise ValueError("control_stop_mismatch")
                    stops[key] = event
                elif kind == "ADMITTED":
                    if (action not in {"CREATE_SESSION", "BROWSER_PAYMENT"} or not isinstance(ref, str)
                        or not ref or ref in admissions or stop is not None or key in stops
                        or any(a["operation_id"] == op and a["action"] == action for a in admissions.values())):
                        raise ValueError("control_admission_mismatch")
                    admissions[ref] = event
                elif kind == "OUTCOME":
                    prior = admissions.get(ref)
                    if (prior is None or ref in outcomes or any(event[k] != prior[k]
                        for k in ("operation_id", "snapshot_sha256", "action"))
                        or details.get("outcome") not in {"COMPLETED", "NO_EFFECT", "UNKNOWN"}
                        or stop is not None):
                        raise ValueError("control_outcome_mismatch")
                    self._validate_control_outcome(details)
                    outcomes[ref] = event
                elif kind == "DENIED":
                    if (action not in {"CREATE_SESSION", "BROWSER_PAYMENT"} or ref is not None
                        or details.get("decision") not in {"DENY", "CONFIRMATION_REQUIRED", "INDETERMINATE"}):
                        raise ValueError("control_denial_mismatch")
                    if stop is not None:
                        native = self._read_mandate_shutdown(con, key)
                        if (not native or stop != native["event_id"] or details["decision"] != "DENY"):
                            raise ValueError("control_denial_stop_mismatch")
                elif kind == "RECOVERY_OBSERVED":
                    if action is not None or ref is not None:
                        raise ValueError("control_recovery_mismatch")
                    if stop is not None:
                        native = self._read_mandate_shutdown(con, key)
                        if not native or stop != native["event_id"]:
                            raise ValueError("control_recovery_stop_mismatch")
                    related = details.get("admission_refs", [])
                    if any(a not in admissions or admissions[a]["operation_id"] != op for a in related):
                        raise ValueError("control_recovery_admission_mismatch")
                else:
                    raise ValueError("control_kind_invalid")
                events.append(event)
            except (TypeError, ValueError, KeyError, OverflowError) as error:
                raise StripeCheckoutError("stored_action_control_fact_invalid") from error
        return events, keys, admissions, outcomes, stops

    def begin_stored_action(self, operation_id, *, expected_sha256, action):
        """Commit one admission before releasing the transaction and calling a provider."""
        if action not in {"CREATE_SESSION", "BROWSER_PAYMENT"}:
            raise StripeCheckoutError("stored_action_invalid")
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            ctx, recorded_at = self._load_authority_in_transaction(con, operation_id, expected_sha256)
            _, _, admissions, outcomes, _ = self._control_history(con)
            stop = self._read_mandate_shutdown(con, self._mandate_key(ctx))
            withdrawn = self._read_withdrawal(con, operation_id, expected_sha256, ctx, recorded_at)
            previous = next((a for a in admissions.values() if a["operation_id"] == operation_id
                             and a["action"] == action), None)
            row = con.execute("SELECT * FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
            decision, reason = "ALLOW", "stored_action_admitted"
            if stop:
                decision, reason = "DENY", "mandate_shutdown"
            elif withdrawn:
                decision, reason = "CONFIRMATION_REQUIRED", "confirmation_withdrawn"
            elif previous and (previous["admission_ref"] not in outcomes
                               or outcomes[previous["admission_ref"]]["details"]["outcome"] == "UNKNOWN"):
                decision, reason = "INDETERMINATE", "original_action_unresolved_query_original"
            elif (action == "CREATE_SESSION" and (row["state"] != "CREATED" or row["session_id"] is not None)
                  or action == "BROWSER_PAYMENT" and (row["state"] != "SESSION_OPEN" or not row["session_id"])):
                decision, reason = "DENY", "stored_action_original_state_invalid"
            elif previous:
                decision, reason = "DENY", "original_action_already_admitted"
            ref = "admission-" + uuid4().hex if decision == "ALLOW" else None
            event = self._append_control(con, kind="ADMITTED" if ref else "DENIED",
                operation_id=operation_id, snapshot_sha256=expected_sha256, action=action,
                admission_ref=ref, stop_event_ref=stop["event_id"] if stop else None,
                details={"decision": decision, "reason": reason})
            return {k: event[k] for k in ("operation_id", "snapshot_sha256", "action",
                    "admission_ref", "sequence", "stop_event_ref")} | {"decision": decision, "reason": reason}

    @staticmethod
    def _validate_control_outcome(details):
        """Apply the same terminal evidence contract on append and trusted read."""
        from .models import Decision

        if not isinstance(details, dict) or set(details) != {"outcome", "result_ref", "gate_record"}:
            raise StripeCheckoutError("stored_action_outcome_invalid")
        outcome, result_ref, gate = (details[k] for k in ("outcome", "result_ref", "gate_record"))
        if outcome not in ("COMPLETED", "NO_EFFECT", "UNKNOWN"):
            raise StripeCheckoutError("stored_action_outcome_invalid")
        if outcome == "UNKNOWN":
            if result_ref is not None or gate is not None:
                raise StripeCheckoutError("stored_action_unknown_evidence_conflict")
            return
        if outcome == "COMPLETED":
            if not isinstance(result_ref, str) or not result_ref.strip():
                raise StripeCheckoutError("stored_action_completion_evidence_missing")
        elif result_ref is not None:
            raise StripeCheckoutError("stored_action_result_conflict")
        if (not isinstance(gate, dict) or set(gate) != {"decision", "callback_count", "reason"}
            or not isinstance(gate["decision"], str)
            or gate["decision"] not in {d.value for d in Decision}
            or type(gate["callback_count"]) is not int
            or gate["callback_count"] != (1 if outcome == "COMPLETED" else 0)
            or (outcome == "COMPLETED") != (gate["decision"] == "ALLOW")
            or not isinstance(gate["reason"], list)
            or any(not isinstance(reason, str) or not reason.strip() for reason in gate["reason"])):
            raise StripeCheckoutError("stored_action_gate_mismatch")

    def finish_stored_action(self, admission_ref, *, outcome, result_ref=None, gate_record=None):
        details = dict(outcome=outcome, result_ref=result_ref, gate_record=gate_record)
        self._validate_control_outcome(details)
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            _, _, admissions, outcomes, _ = self._control_history(con)
            prior = admissions.get(admission_ref)
            if prior is None:
                raise StripeCheckoutError("stored_action_admission_unknown")
            existing = outcomes.get(admission_ref)
            if existing:
                if existing["details"] != details:
                    raise StripeCheckoutError("stored_action_outcome_conflict")
                return existing
            return self._append_control(con, kind="OUTCOME", operation_id=prior["operation_id"],
                snapshot_sha256=prior["snapshot_sha256"], action=prior["action"],
                admission_ref=admission_ref, details=details)

    def get_shutdown_control_view(self, operation_id, *, expected_sha256):
        with self._open() as con:
            con.execute("BEGIN")
            ctx, _ = self._load_authority_in_transaction(con, operation_id, expected_sha256)
            key = self._mandate_key(ctx)
            events, keys, admissions, outcomes, stops = self._control_history(con)
            stop = self._read_mandate_shutdown(con, key)
            stop_sequence = stops[key]["sequence"] if key in stops else None
            events = [e for e in events if keys[(e["operation_id"], e["snapshot_sha256"])] == key]
            relevant_states = {}
            for row in con.execute("SELECT operation_id,snapshot_sha256 FROM authority_contexts"):
                other, _ = self._load_authority_in_transaction(con, row["operation_id"], row["snapshot_sha256"])
                if self._mandate_key(other) == key:
                    relevant_states[row["operation_id"]] = con.execute(
                        "SELECT state FROM operations WHERE operation_id=?", (row["operation_id"],)).fetchone()[0]
            attempts, unresolved = [], []
            unresolved_ops = {op for op, state in relevant_states.items() if state == "UNKNOWN"}
            for e in events:
                if e["kind"] != "ADMITTED":
                    continue
                ref = e["admission_ref"]
                outcome = outcomes.get(ref, {}).get("details", {})
                status = outcome.get("outcome", "ADMITTED")
                op = e["operation_id"]
                attempts.append({k: e[k] for k in ("operation_id", "action", "snapshot_sha256", "admission_ref")}
                    | dict(admission_sequence=e["sequence"], outcome=status, result_ref=outcome.get("result_ref")))
                if relevant_states[op] not in {"PAID_CONFIRMED", "CANCELLED"} and (
                    status in {"ADMITTED", "UNKNOWN"} or
                    (status == "COMPLETED" and e["action"] == "BROWSER_PAYMENT")):
                    unresolved.append(ref)
                    unresolved_ops.add(op)
            return dict(source="NATIVE_STORED_ACTION_CONTROL", operation_id=operation_id,
                stop_event_ref=stop["event_id"] if stop else None, stop_sequence=stop_sequence,
                order_status="LEGACY_UNRECORDED" if stop and stop_sequence is None else "NATIVE",
                new_actions_blocked=bool(stop), state=("ACTIVE" if not stop else
                    "STOP_ACCEPTED_PENDING" if unresolved or unresolved_ops else "STOP_ACCEPTED_LOCAL_QUIESCENT"),
                attempts=attempts, events=events, unresolved_admission_refs=unresolved,
                unresolved_operation_ids=sorted(unresolved_ops))

    def record_mandate_shutdown(self, anchor_operation_id, *, expected_sha256,
                                subject_ref, mandate_id, authority_version,
                                event_id, received_at):
        """Trusted local user-control boundary; authentication is upstream."""
        with self._open() as con:
            con.execute("BEGIN IMMEDIATE")
            context, recorded_at = self._load_authority_in_transaction(
                con, anchor_operation_id, expected_sha256
            )
            fact = self._mandate_shutdown_fact(
                anchor_operation_id, expected_sha256, context, recorded_at,
                subject_ref=subject_ref, mandate_id=mandate_id,
                authority_version=authority_version, event_id=event_id,
                received_at=received_at,
            )
            self._control_history(con)
            existing = self._read_mandate_shutdown(con, self._mandate_key(context))
            if existing is not None:
                if existing != fact:
                    raise StripeCheckoutError("mandate_shutdown_conflict")
                return existing
            try:
                con.execute(
                    """INSERT INTO mandate_shutdowns
                       (subject_ref,mandate_id,authority_version,event_id,
                        anchor_operation_id,anchor_snapshot_sha256,received_at,source)
                       VALUES (:subject_ref,:mandate_id,:authority_version,:event_id,
                               :anchor_operation_id,:anchor_snapshot_sha256,:received_at,:source)""",
                    fact,
                )
            except sqlite3.IntegrityError:
                raise StripeCheckoutError("mandate_shutdown_conflict") from None
            self._append_control(con, kind="STOP_ACCEPTED", operation_id=anchor_operation_id,
                snapshot_sha256=expected_sha256, stop_event_ref=event_id, details={"receipt": fact})
            return fact

    def get_mandate_shutdown(self, operation_id, *, expected_sha256):
        """Derive the stop key from the verified original operation, never caller input."""
        with self._open() as con:
            con.execute("BEGIN")
            context, _ = self._load_authority_in_transaction(
                con, operation_id, expected_sha256
            )
            return self._read_mandate_shutdown(con, self._mandate_key(context))

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
            con.execute("BEGIN IMMEDIATE")
            original = con.execute("SELECT snapshot_sha256 FROM authority_contexts WHERE operation_id=?",
                                   (operation_id,)).fetchone()
            if original:
                digest = original["snapshot_sha256"]
                ctx, _ = self._load_authority_in_transaction(con, operation_id, digest)
                _, _, admissions, _, _ = self._control_history(con)
                stop = self._read_mandate_shutdown(con, self._mandate_key(ctx))
                native = con.execute("SELECT * FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
                if native["session_id"] != payment.provider_ref:
                    raise StripeCheckoutError("recovery_original_payment_mismatch")
                self._append_control(con, kind="RECOVERY_OBSERVED", operation_id=operation_id,
                    snapshot_sha256=digest, stop_event_ref=stop["event_id"] if stop else None,
                    details={"admission_refs": [ref for ref, a in admissions.items() if a["operation_id"] == operation_id],
                        "provider_ref": payment.provider_ref, "observed_status": observation.status.value,
                        "effective_status": outcome.effective_status.value, "recovery_status": outcome.recovery_status.value,
                        "next_action": outcome.next_action, "retry_allowed": outcome.retry_allowed,
                        "operation_state": native["state"]})
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
