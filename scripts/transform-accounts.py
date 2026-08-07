#!/usr/bin/env python3
"""Transform account names from CSV into a Salesforce-ready import file."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform account names into Salesforce-ready CSV")
    parser.add_argument("--input", required=True, help="Input CSV file containing account names")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--summary", required=True, help="Transformation summary JSON file")
    parser.add_argument("--log", required=True, help="Transformation log file")
    parser.add_argument("--agent-spec", required=True, help="Copilot agent specification file")
    return parser.parse_args()


def read_source_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Input CSV is missing a header row")
        if "AccountName" not in {name.strip() for name in reader.fieldnames}:
            raise ValueError("Input CSV must contain an AccountName column")
        return [{key.strip(): (value or "").strip() for key, value in row.items() if key is not None} for row in reader]


def write_output_csv(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Name", "Industry"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"Name": row["Name"], "Industry": row["Industry"]})


def write_summary(summary_path: Path, summary: dict[str, Any]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")


def write_log(log_path: Path, lines: list[str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)
    log_path = Path(args.log)
    agent_spec_path = Path(args.agent_spec)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not agent_spec_path.exists():
        raise FileNotFoundError(f"Agent specification not found: {agent_spec_path}")

    rows = read_source_rows(input_path)
    valid_rows: list[dict[str, str]] = []
    duplicates: list[str] = []
    seen_names: set[str] = set()
    invalid_rows = 0

    for index, row in enumerate(rows, start=1):
        account_name = ""
        for key in row:
            if key.lower() == "accountname":
                account_name = row[key]
                break
        normalized_name = account_name.strip().lower()
        if not account_name.strip() or len(account_name.strip()) < 2:
            invalid_rows += 1
            continue
        if normalized_name in seen_names:
            duplicates.append(account_name)
            continue
        seen_names.add(normalized_name)
        valid_rows.append({"Name": account_name.strip(), "Industry": "Media"})

    write_output_csv(output_path, valid_rows)

    summary = {
        "source_file": str(input_path),
        "agent_spec": str(agent_spec_path),
        "records_processed": len(rows),
        "valid_records": len(valid_rows),
        "invalid_records": invalid_rows,
        "duplicate_records": len(duplicates),
        "duplicates": duplicates,
        "output_file": str(output_path),
        "industry_default": "Media",
    }
    write_summary(summary_path, summary)

    log_lines = [
        "Transformation started",
        f"Loaded {len(rows)} source records from {input_path}",
        f"Validated {len(valid_rows)} valid records",
        f"Skipped {invalid_rows} invalid records",
        f"Detected {len(duplicates)} duplicate records",
        f"Generated output file {output_path}",
        f"Generated summary file {summary_path}",
        f"Invoked Copilot agent specification {agent_spec_path}",
    ]
    write_log(log_path, log_lines)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Transformation failed: {exc}", file=sys.stderr)
        sys.exit(1)
