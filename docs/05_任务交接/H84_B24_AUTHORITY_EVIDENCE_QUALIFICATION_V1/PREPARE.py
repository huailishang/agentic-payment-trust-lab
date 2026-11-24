"""Generate the H84 isolated candidate from the independently accepted H78 collector.
No service, credential, or network operation is performed by this script.
"""
from pathlib import Path
import hashlib
import shutil

TASK = Path(__file__).resolve().parent
PARENT = TASK.parent / "H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1"
SOURCE = PARENT / "WORKLOAD.py"
EXPECTED = "b0817be01d5ad1cb756ccd122add5afc2e09588060d948806b749e1485c1aaf8"

def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    source = SOURCE.read_text(encoding="utf-8")
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old[:120]
        source = source.replace(old, new)
    start = source.index("    def authorize(self):")
    end = source.index("    def budget(self):", start)
    source = source[:start] + '''    def authorize(self):
        from MEASURE import authorize
        authorize(self)

''' + source[end:]
    # A second workload is not the comparison; use the SAME UID on both sides.
    start = source.index('        self.event("nonmatching_fetch_start"')
    end = source.index("        issued = int(time.time())", start)
    source = source[:start] + source[end:]
    replace('entry_cli_success=True, unmatched_uid={"uid": 1002, "exit_code": denied.returncode, "identity_count": 0, "socket_connected": True})', 'entry_cli_success=True)')
    replace('        self.event("holder_signature_end", signing_uid=1001)', '''        self.event("holder_signature_end", signing_uid=1001)
        from MEASURE import transition
        transition(self, server, management, entry_id, processes)''')
    # Add a fresh subdirectory for a same-UID fetch after deletion. Never read
    # stale certificate files as evidence of a current source response.
    replace('    if args.operation in ("matching", "nonmatching", "signing"):', '    if args.operation in ("matching", "nonmatching", "transition", "signing"):')
    replace('    if args.operation in ("matching", "nonmatching"):\n        command =', '''    if args.operation in ("matching", "nonmatching", "transition"):
        if args.operation == "transition":
            home = home / "after"
            home.mkdir(mode=0o700, exist_ok=True)
            home = home / str(os.getpid())
            home.mkdir(mode=0o700, exist_ok=False)
            need(not home.is_symlink() and home.stat().st_uid == uid and stat.S_IMODE(home.stat().st_mode) == 0o700, "after directory")
        command =''')
    replace('            if operation in ("matching", "nonmatching"):', '            if operation in ("matching", "nonmatching", "transition"):')
    replace('str(self.base / ("u" + str(uid))) ]', 'str(self.base / ("u" + str(uid)) / "after" / str(observed["pid"]) if operation == "transition" else self.base / ("u" + str(uid))) ]')
    replace('choices=("matching", "nonmatching", "inspect", "inspect_negative", "signing")', 'choices=("matching", "nonmatching", "inspect", "inspect_negative", "transition", "signing")')
    replace('return 0 if self.state["status"] == "ISSUER_FETCH_SIGNATURE_CAPTURED" and clean else 1', 'return 0 if self.state["status"] == "H84_TRANSITION_OBSERVED" and clean else 1')
    # The original collector creates and chowns an unused UID1002 directory;
    # do not create or use a second workload in the H84 measurement.
    replace(', ("u1002", 0o700)', '')
    replace('for uid in (1001, 1002):', 'for uid in (1001,):')
    output = TASK / "WORKLOAD.py"
    if output.exists():
        assert output.read_text(encoding="utf-8") == source, "candidate drift"
    else:
        output.write_text(source, encoding="utf-8")
    lock = TASK / "BINARY_MEMBER_LOCK.json"
    if not lock.exists():
        shutil.copyfile(PARENT / lock.name, lock)
    assert lock.read_bytes() == (PARENT / lock.name).read_bytes()
    compile(source, str(output), "exec")
    print("CANDIDATE_GENERATED", hashlib.sha256(output.read_bytes()).hexdigest())

if __name__ == "__main__":
    main()
