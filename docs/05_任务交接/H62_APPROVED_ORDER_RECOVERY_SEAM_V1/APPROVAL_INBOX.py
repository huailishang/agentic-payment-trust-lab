"""Local-only human-operator reconciliation approval register.

Reads live merchant snapshots and a closed synthetic PSP source. Writes only to
a distinct approval ledger. Committed order consumption is read from the merchant
transaction database; recording approval never executes an order.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import uuid


class ApprovalDenied(Exception):
    def __init__(self, code):
        self.code = str(code)
        super().__init__(self.code)


def _deny(code):
    raise ApprovalDenied(code)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _text(value, max_length=None):
    return (isinstance(value, str) and bool(value.strip()) and
            (max_length is None or len(value) <= max_length))


def _fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        _deny("INVALID_REQUEST_FIELDS")


class ApprovalInbox:
    """Trusted-configuration-bound approval: no order, refund, charge, or consume."""

    def __init__(self, *, transactions_path, psp_path, ledger_path,
                 operator_context, now):
        self.tx = Path(transactions_path).resolve()
        self.psp = Path(psp_path).resolve()
        self.ledger = Path(ledger_path).resolve()
        if len({self.tx, self.psp, self.ledger}) != 3:
            _deny("SOURCE_LEDGER_NOT_ISOLATED")
        try:
            ledger_exists = self.ledger.stat() is not None
        except FileNotFoundError:
            ledger_exists = False
        except OSError:
            _deny("SOURCE_LEDGER_NOT_ISOLATED")
        if ledger_exists:
            try:
                if (os.path.samefile(self.ledger, self.tx) or
                        os.path.samefile(self.ledger, self.psp)):
                    _deny("SOURCE_LEDGER_NOT_ISOLATED")
            except OSError:
                _deny("SOURCE_LEDGER_NOT_ISOLATED")
        self.context = operator_context
        self.now = now
        if not callable(now):
            _deny("INVALID_TRUSTED_CLOCK")
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(self._ledger_connection()) as conn:
                # Existing ledgers need no DDL/write lock during construction.
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                if not {"approvals", "approval_events"}.issubset(tables):
                    conn.execute("""CREATE TABLE IF NOT EXISTS approvals (
                        approval_id TEXT PRIMARY KEY,
                        operator_id TEXT NOT NULL,
                        request_key TEXT NOT NULL,
                        checkout_id TEXT NOT NULL,
                        payment_ref TEXT NOT NULL,
                        record_json TEXT NOT NULL,
                        approve_request_json TEXT NOT NULL,
                        revoke_request_json TEXT,
                        UNIQUE(operator_id,request_key),
                        UNIQUE(checkout_id,payment_ref)
                    )""")
                    conn.execute("""CREATE TABLE IF NOT EXISTS approval_events (
                        approval_id TEXT NOT NULL,
                        seq INTEGER NOT NULL,
                        kind TEXT NOT NULL,
                        operator_id TEXT NOT NULL,
                        source_digest TEXT NOT NULL,
                        at INTEGER NOT NULL,
                        request_json TEXT NOT NULL,
                        PRIMARY KEY(approval_id,seq)
                    )""")
                    conn.commit()
        except sqlite3.Error:
            _deny("APPROVAL_LEDGER_UNAVAILABLE")

    def _ledger_connection(self):
        connection = sqlite3.connect(str(self.ledger), timeout=0)
        connection.row_factory = sqlite3.Row
        return connection

    def _clock(self):
        value = self.now()
        if type(value) is not int:
            _deny("INVALID_TRUSTED_CLOCK")
        return value

    def _trusted(self):
        ctx = self.context
        if not isinstance(ctx, dict) or not _text(ctx.get("operator_id")):
            _deny("OPERATOR_CONTEXT_INVALID")
        if ctx.get("active") is not True:
            _deny("OPERATOR_INACTIVE")
        if (not isinstance(ctx.get("roles"), list) or
                "RECONCILIATION_APPROVER" not in ctx["roles"]):
            _deny("OPERATOR_ROLE_DENIED")
        if not _text(ctx.get("policy_version")):
            _deny("OPERATOR_POLICY_INVALID")
        try:
            return ctx["operator_id"], ctx["policy_version"], _digest(ctx)
        except (ValueError, TypeError):
            _deny("OPERATOR_CONTEXT_INVALID")

    @staticmethod
    def _read_source(path, table):
        if (not path.is_file() or Path(str(path) + "-wal").exists()
                or Path(str(path) + "-shm").exists()):
            _deny("SOURCE_UNAVAILABLE")
        try:
            with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                quoted = '"' + table.replace('"', '""') + '"'
                return [dict(row) for row in conn.execute("SELECT * FROM " + quoted)]
        except (sqlite3.Error, OSError, ValueError):
            _deny("SOURCE_UNAVAILABLE")

    @staticmethod
    def _transaction_rows(conn):
        """Read one live transaction snapshot, including any consumption receipt."""
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        result = {}
        for table in ("checkouts", "h50_attempts", "h53_authorizations",
                      "h50_confirmations", "inventory", "orders", "h62_consumptions"):
            result[table] = ([dict(row) for row in conn.execute(
                'SELECT * FROM "' + table + '" ORDER BY rowid')]
                if table in names else [])
        return result

    def _live_transaction_rows(self):
        with closing(sqlite3.connect(self.tx.as_uri() + "?mode=ro", uri=True,
                                     timeout=0)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN")
            return self._transaction_rows(conn)

    def _source(self, checkout_id, *, transaction_rows=None):
        if not _text(checkout_id):
            _deny("INVALID_CHECKOUT_ID")
        tables = (self._live_transaction_rows()
                  if transaction_rows is None else transaction_rows)

        def single(table, key, value):
            return next((row for row in tables[table] if row[key] == value), None)

        checkout = single("checkouts", "id", checkout_id)
        attempt = single("h50_attempts", "checkout_id", checkout_id)
        authorization = single("h53_authorizations", "checkout_id", checkout_id)
        confirmation = (single("h50_confirmations", "confirmation_ref",
                        authorization["confirmation_ref"]) if authorization else None)
        receipt = (next((r for r in self._read_source(self.psp, "receipts")
                         if r["payment_ref"] == attempt["payment_ref"]), None)
                   if attempt else None)
        return {
            "checkout": checkout, "attempt": attempt,
            "authorization": authorization, "confirmation": confirmation,
            "receipt": receipt,
            "inventory": sorted(tables["inventory"], key=lambda r: r["product_id"]),
            "orders": sorted(tables["orders"], key=lambda r: r["id"]),
        }

    def _consumption(self, record, *, transaction_rows=None):
        """A verified committed receipt is the only authority for a consumed result."""
        tables = (self._live_transaction_rows()
                  if transaction_rows is None else transaction_rows)
        matches = [r for r in tables["h62_consumptions"]
                   if (r["approval_id"] == record["approval_id"]
                       or r["checkout_id"] == record["checkout_id"]
                       or r["payment_ref"] == record["payment_ref"])]
        if not matches:
            return None
        if len(matches) != 1:
            _deny("CONSUMPTION_BINDING_INVALID")
        receipt = matches[0]
        if any(receipt[k] != record[k] for k in (
                "approval_id", "checkout_id", "payment_ref",
                "source_digest", "context_digest")):
            _deny("CONSUMPTION_BINDING_INVALID")
        response = json.loads(receipt["response_json"])
        order = next((r for r in tables["orders"]
                      if r["id"] == receipt["order_id"]), None)
        checkout = next((r for r in tables["checkouts"]
                         if r["id"] == record["checkout_id"]), None)
        if (not order or not checkout or checkout["status"] != "completed"
                or response.get("status") != "RECOVERED"
                or response.get("order_id") != receipt["order_id"]
                or response.get("notification_status") != "PENDING_NOT_SENT"
                or json.loads(order["data"]).get("checkout_id") != record["checkout_id"]
                or json.loads(checkout["data"]).get("order", {}).get("id")
                != receipt["order_id"]):
            _deny("CONSUMPTION_RESULT_INCONSISTENT")
        return receipt

    @staticmethod
    def _eligible(view, checkout_id, payment_ref=None):
        try:
            checkout = view["checkout"]
            attempt = view["attempt"]
            authorization = view["authorization"]
            confirmation = view["confirmation"]
            receipt = view["receipt"]
            if not all(isinstance(x, dict) for x in
                       (checkout, attempt, authorization, confirmation, receipt)):
                return False
            if view["orders"]:
                return False
            if checkout["id"] != checkout_id or checkout["status"] != "ready_for_complete":
                return False
            if attempt["checkout_id"] != checkout_id or attempt["state"] != "IN_FLIGHT":
                return False
            if payment_ref is not None and attempt["payment_ref"] != payment_ref:
                return False
            if receipt["payment_ref"] != attempt["payment_ref"]:
                return False
            if (authorization["checkout_id"] != checkout_id or
                    authorization["decision"] != "ALLOW" or
                    confirmation["confirmation_ref"] != authorization["confirmation_ref"] or
                    confirmation["checkout_id"] != checkout_id or
                    confirmation["revoked"] != 0):
                return False
            snapshot = json.loads(attempt["snapshot_json"])
            confirmed = json.loads(confirmation["snapshot_json"])
            paid = json.loads(receipt["snapshot_json"])
            current = json.loads(checkout["data"])
            if snapshot != confirmed or snapshot != paid:
                return False
            if (snapshot.get("checkout_id") != checkout_id or
                    not _text(snapshot.get("merchant")) or
                    not _text(snapshot.get("payee"))):
                return False
            for name in ("currency", "line_items", "totals", "fulfillment"):
                if current.get(name) != snapshot.get(name):
                    return False
            if current.get("id") != checkout_id:
                return False
            return True
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False

    def inspect(self, checkout_id):
        try:
            source = self._source(checkout_id)
            eligible = self._eligible(source, checkout_id)
            attempt = source.get("attempt")
            payment_ref = attempt["payment_ref"] if attempt else None
            digest = _digest(source)
        except (ApprovalDenied, ValueError, TypeError):
            eligible, digest, payment_ref = False, None, None
        return {
            "eligible": eligible, "source_digest": digest,
            "checkout_id": checkout_id, "payment_ref": payment_ref,
            "execution_enabled": False,
        }

    def _read_result(self, conn, row, *, transaction_rows=None):
        if row is None:
            _deny("APPROVAL_NOT_FOUND")
        record = json.loads(row["record_json"])
        events = [{
            "seq": e["seq"], "kind": e["kind"], "approval_id": e["approval_id"],
            "operator_id": e["operator_id"], "source_digest": e["source_digest"],
            "at": e["at"], "request": json.loads(e["request_json"]),
        } for e in conn.execute(
            "SELECT * FROM approval_events WHERE approval_id=? ORDER BY seq",
            (row["approval_id"],)
        )]
        consumed = self._consumption(record, transaction_rows=transaction_rows)
        if consumed is not None:
            operator, _, context_digest = self._trusted()
            if (operator != record["operator_id"]
                    or context_digest != record["context_digest"]):
                _deny("OPERATOR_CONTEXT_MISMATCH")
            return {"record": record, "events": events, "current": False,
                    "effective_state": "APPROVAL_CONSUMED",
                    "execution_enabled": False, "order_id": consumed["order_id"]}
        if any(e["kind"] == "REVOKED" for e in events):
            state = "APPROVAL_REVOKED"
        else:
            try:
                _, _, current_digest = self._trusted()
                if current_digest != record["context_digest"]:
                    state = "APPROVAL_STALE_CONTEXT"
                elif self._clock() >= record["expires_at"]:
                    state = "APPROVAL_EXPIRED"
                else:
                    try:
                        source = self._source(record["checkout_id"])
                        good = (self._eligible(source, record["checkout_id"],
                                               record["payment_ref"]) and
                                _digest(source) == record["source_digest"])
                    except (ApprovalDenied, ValueError, TypeError):
                        good = False
                    state = "APPROVAL_CURRENT" if good else "APPROVAL_STALE_SOURCE"
            except ApprovalDenied:
                state = "APPROVAL_STALE_CONTEXT"
        return {"record": record, "events": events,
                "current": state == "APPROVAL_CURRENT",
                "effective_state": state, "execution_enabled": False}

    def show(self, approval_id):
        if not _text(approval_id):
            _deny("INVALID_APPROVAL_ID")
        try:
            with closing(self._ledger_connection()) as conn:
                row = conn.execute("SELECT * FROM approvals WHERE approval_id=?",
                                   (approval_id,)).fetchone()
                return self._read_result(conn, row)
        except sqlite3.Error:
            _deny("APPROVAL_LEDGER_UNAVAILABLE")

    def approve(self, request):
        _fields(request, (
            "request_key", "checkout_id", "payment_ref",
            "expected_source_digest", "disposition", "reason", "expires_at"))
        for name in ("request_key", "checkout_id", "payment_ref",
                     "expected_source_digest", "reason"):
            if not _text(request[name]):
                _deny("INVALID_APPROVAL_REQUEST")
        if len(request["reason"]) > 500:
            _deny("INVALID_APPROVAL_REASON")
        if (request["disposition"] != "ORDER_COMPLETION" or
                not _text(request["disposition"])):
            _deny("UNSUPPORTED_DISPOSITION")
        if type(request["expires_at"]) is not int:
            _deny("INVALID_EXPIRY")
        operator, policy, context_digest = self._trusted()
        try:
            with closing(self._ledger_connection()) as conn:
                conn.execute("BEGIN IMMEDIATE")
                original = conn.execute(
                    "SELECT * FROM approvals WHERE operator_id=? AND request_key=?",
                    (operator, request["request_key"])
                ).fetchone()
                if original:
                    if json.loads(original["approve_request_json"]) != request:
                        _deny("IDEMPOTENCY_CONFLICT")
                    return self._read_result(conn, original)
                now = self._clock()
                if not now < request["expires_at"] <= now + 600:
                    _deny("INVALID_EXPIRY")
                source = self._source(request["checkout_id"])
                if not self._eligible(source, request["checkout_id"],
                                      request["payment_ref"]):
                    _deny("SOURCE_NOT_ELIGIBLE")
                source_digest = _digest(source)
                if request["expected_source_digest"] != source_digest:
                    _deny("SOURCE_DIGEST_MISMATCH")
                existing = conn.execute(
                    "SELECT approval_id FROM approvals WHERE checkout_id=? AND payment_ref=?",
                    (request["checkout_id"], request["payment_ref"])
                ).fetchone()
                if existing:
                    _deny("ACTIVE_APPROVAL_EXISTS")
                approval_id = "h60-approval-" + uuid.uuid4().hex
                record = {
                    "approval_id": approval_id, "request_key": request["request_key"],
                    "checkout_id": request["checkout_id"],
                    "payment_ref": request["payment_ref"],
                    "source_digest": source_digest, "context_digest": context_digest,
                    "operator_id": operator, "policy_version": policy,
                    "disposition": request["disposition"], "reason": request["reason"],
                    "expires_at": request["expires_at"],
                }
                conn.execute("""INSERT INTO approvals
                    (approval_id, operator_id, request_key, checkout_id, payment_ref,
                     record_json, approve_request_json) VALUES (?,?,?,?,?,?,?)""",
                    (approval_id, operator, request["request_key"],
                     request["checkout_id"], request["payment_ref"],
                     _canonical(record), _canonical(request)))
                conn.execute("""INSERT INTO approval_events
                    (approval_id,seq,kind,operator_id,source_digest,at,request_json)
                    VALUES (?,?,?,?,?,?,?)""",
                    (approval_id, 1, "APPROVED", operator, source_digest,
                     now, _canonical(request)))
                conn.commit()
                return self._read_result(conn, conn.execute(
                    "SELECT * FROM approvals WHERE approval_id=?",
                    (approval_id,)
                ).fetchone())
        except ApprovalDenied:
            raise
        except sqlite3.Error:
            _deny("APPROVAL_LEDGER_UNAVAILABLE")

    def revoke(self, request):
        _fields(request, ("approval_id", "request_key", "reason"))
        if not all(_text(request[k]) for k in ("approval_id", "request_key", "reason")):
            _deny("INVALID_REVOKE_REQUEST")
        if len(request["reason"]) > 500:
            _deny("INVALID_REVOKE_REASON")
        operator, _, _ = self._trusted()
        try:
            # Every revoke entry point, including CLI, uses this same lock order.
            with closing(self._ledger_connection()) as conn:
                conn.execute("BEGIN IMMEDIATE")
                with closing(sqlite3.connect(self.tx.as_uri() + "?mode=rw",
                                             uri=True, timeout=0)) as tx:
                    tx.row_factory = sqlite3.Row
                    tx.execute("BEGIN IMMEDIATE")
                    tables = self._transaction_rows(tx)
                    row = conn.execute("SELECT * FROM approvals WHERE approval_id=?",
                                       (request["approval_id"],)).fetchone()
                    if row is None:
                        _deny("APPROVAL_NOT_FOUND")
                    if row["operator_id"] != operator:
                        _deny("REVOKE_NOT_OWNER")
                    record = json.loads(row["record_json"])
                    if self._consumption(record, transaction_rows=tables):
                        # Late revocation must not falsely report that it prevented an order.
                        return self._read_result(conn, row, transaction_rows=tables)
                    if row["revoke_request_json"]:
                        if json.loads(row["revoke_request_json"]) != request:
                            _deny("REVOKE_CONFLICT")
                        return self._read_result(conn, row, transaction_rows=tables)
                    conn.execute("UPDATE approvals SET revoke_request_json=? WHERE approval_id=?",
                                 (_canonical(request), request["approval_id"]))
                    source_digest = record["source_digest"]
                    conn.execute("""INSERT INTO approval_events
                        (approval_id,seq,kind,operator_id,source_digest,at,request_json)
                        VALUES (?,?,?,?,?,?,?)""",
                        (request["approval_id"], 2, "REVOKED", operator,
                         source_digest, self._clock(), _canonical(request)))
                    conn.commit()
                    return self._read_result(conn, conn.execute(
                        "SELECT * FROM approvals WHERE approval_id=?",
                        (request["approval_id"],)).fetchone(), transaction_rows=tables)
        except ApprovalDenied:
            raise
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                _deny("APPROVAL_BUSY")
            _deny("APPROVAL_LEDGER_UNAVAILABLE")
        except sqlite3.Error:
            _deny("APPROVAL_LEDGER_UNAVAILABLE")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", required=True)
    parser.add_argument("--psp", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--operator-config", required=True)
    parser.add_argument("--now", required=True, type=int)
    parser.add_argument("command", choices=("inspect", "approve", "revoke", "show"))
    args = parser.parse_args()
    try:
        with Path(args.operator_config).open(encoding="utf-8") as stream:
            context = json.load(stream)
        request = json.load(sys.stdin)
        inbox = ApprovalInbox(transactions_path=args.transactions, psp_path=args.psp,
                              ledger_path=args.ledger, operator_context=context,
                              now=lambda: args.now)
        if args.command == "inspect":
            _fields(request, ("checkout_id",))
            answer = inbox.inspect(request["checkout_id"])
        elif args.command == "show":
            _fields(request, ("approval_id",))
            answer = inbox.show(request["approval_id"])
        elif args.command == "approve":
            answer = inbox.approve(request)
        else:
            answer = inbox.revoke(request)
        print(json.dumps(answer, ensure_ascii=False, sort_keys=True))
    except ApprovalDenied as exc:
        print(json.dumps({"error": exc.code}))
        return 2
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        print(json.dumps({"error": "INVALID_INPUT"}))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
