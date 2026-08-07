#!/usr/bin/env python3
"""Generate an audit report for the Salesforce data load workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an audit report")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--import-results", required=True)
    parser.add_argument("--audit-file", required=True)
    parser.add_argument("--workflow-name", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--github-user", required=True)
    parser.add_argument("--pr-number", default="")
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--approver", default="")
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--org-alias", required=True)
    parser.add_argument("--instance-url", required=True)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    args = parse_args()
    summary_path = Path(args.summary)
    import_results_path = Path(args.import_results)
    audit_path = Path(args.audit_file)
    log_path = Path(args.log_file)

    summary_payload = load_json(summary_path)
    import_payload = load_json(import_results_path)
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    records_processed = int(summary_payload.get("records_processed", 0))
    valid_records = int(summary_payload.get("valid_records", 0))
    invalid_records = int(summary_payload.get("invalid_records", 0))
    duplicate_records = int(summary_payload.get("duplicate_records", 0))
    successful_records = int(import_payload.get("successful_records", 0))
    failed_records = int(import_payload.get("failed_records", 0))

    audit_payload = {
        "workflow_name": args.workflow_name,
        "workflow_run_id": args.workflow_run_id,
        "execution_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trigger_type": args.trigger,
        "github_user": args.github_user,
        "pr_number": args.pr_number,
        "github_commit_sha": args.commit_sha,
        "approver": args.approver or "pending",
        "source_file_name": args.source_file,
        "salesforce_org_alias": args.org_alias,
        "salesforce_instance_url": args.instance_url,
        "records_processed": records_processed,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "duplicate_records": duplicate_records,
        "successfully_inserted_records": successful_records,
        "failed_records": failed_records,
        "salesforce_job_information": import_payload.get("job_information", {}),
        "error_details": [],
        "overall_execution_status": "succeeded" if failed_records == 0 else "partially_failed",
        "log_file": str(log_path),
    }

    if failed_records > 0:
        audit_payload["error_details"] = [entry.get("error", "") for entry in import_payload.get("records", []) if entry.get("status") == "failed"]

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8") as handle:
        json.dump(audit_payload, handle, indent=2)
        handle.write("\n")

    print(json.dumps(audit_payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Audit report generation failed: {exc}", file=sys.stderr)
        sys.exit(1)
