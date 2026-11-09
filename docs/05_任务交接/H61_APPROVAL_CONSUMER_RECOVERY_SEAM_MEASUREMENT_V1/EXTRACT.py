"""H61 source-only extraction. Never imports or invokes business code."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    output = parser.parse_args().out.resolve()
    relative = output.relative_to((TASK / "evidence").resolve())
    if (len(relative.parts) != 3 or relative.parts[0] not in {"executor", "evaluator"}
            or not relative.parts[1].startswith("run_")
            or len(relative.parts[1]) != 8
            or not relative.parts[1][4:].isdigit()
            or relative.parts[2] != "EXTRACTION.json"):
        raise ValueError("Output must be a new role/run_NNNN/EXTRACTION.json")
    if output.exists() or not output.parent.is_dir():
        raise ValueError("Reserved output directory required; overwrites forbidden")
    lock = json.loads((TASK / "INPUTS.json").read_text(encoding="utf-8"))
    files = {}
    for name, expected in lock["source_files"].items():
        path = ROOT / name
        sha = digest(path)
        if sha != expected["sha256"]:
            raise ValueError("Source file changed")
        files[name] = {"sha256": sha,
                       "line_count": len(path.read_text(encoding="utf-8").splitlines())}
    databases = {}
    for name, source in lock["source_databases"].items():
        path = (ROOT / source["path"]).resolve()
        if (not path.is_file() or Path(str(path) + "-wal").exists()
                or Path(str(path) + "-shm").exists()):
            raise ValueError("Closed database required")
        before = digest(path)
        if before != source["sha256"]:
            raise ValueError("Source database changed")
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            names = [row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            tables = {}
            for table in names:
                quoted = '"' + table.replace('"', '""') + '"'
                tables[table] = [dict(row) for row in conn.execute(
                    "SELECT * FROM " + quoted + " ORDER BY rowid")]
        if digest(path) != before:
            raise ValueError("Source changed during read")
        databases[name] = {"sha256": before, "tables": tables}
    value = {"schema": "h61-source-extraction/v1", "task_id": TASK.name,
             "files": files, "databases": databases,
             "business_execution_enabled": False}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"files": len(files), "databases": len(databases),
                      "business_execution_enabled": False}))


if __name__ == "__main__":
    main()
