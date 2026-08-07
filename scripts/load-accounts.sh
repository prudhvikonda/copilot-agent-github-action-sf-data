#!/usr/bin/env bash
set -euo pipefail

INPUT_FILE="${INPUT_FILE:-artifacts/transformed-accounts.csv}"
OUTPUT_FILE="${OUTPUT_FILE:-artifacts/salesforce-import-results.json}"

python3 - "$INPUT_FILE" "$OUTPUT_FILE" <<'PY'
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])

if not input_path.exists():
    raise SystemExit(f"Input file not found: {input_path}")

output_path.parent.mkdir(parents=True, exist_ok=True)

results = {
    "source_file": str(input_path),
    "sobject": "Account",
    "operation": "insert",
    "records_processed": 0,
    "successful_records": 0,
    "failed_records": 0,
    "records": [],
    "job_information": {
        "tool": "sf data create record",
        "operation": "insert",
        "sobject": "Account",
    },
}

with input_path.open("r", encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        name = (row.get("Name") or "").strip()
        industry = (row.get("Industry") or "").strip() or "Media"
        results["records_processed"] += 1
        values = f"Name='{name.replace(chr(39), chr(92)+chr(39))}' Industry='{industry.replace(chr(39), chr(92)+chr(39))}'"
        command = ["sf", "data", "create", "record", "--sobject", "Account", "--values", values, "--json"]
        proc = subprocess.run(command, capture_output=True, text=True)
        if proc.returncode == 0:
            payload = json.loads(proc.stdout or "{}")
            record_id = payload.get("id") or payload.get("result", {}).get("id") or ""
            results["successful_records"] += 1
            results["records"].append({
                "name": name,
                "industry": industry,
                "status": "success",
                "record_id": record_id,
            })
        else:
            results["failed_records"] += 1
            results["records"].append({
                "name": name,
                "industry": industry,
                "status": "failed",
                "error": (proc.stderr or proc.stdout).strip(),
            })

with output_path.open("w", encoding="utf-8") as handle:
    json.dump(results, handle, indent=2)
    handle.write("\n")

print(json.dumps(results, indent=2))
PY
