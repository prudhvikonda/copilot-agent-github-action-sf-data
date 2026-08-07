#!/usr/bin/env bash
set -euo pipefail

LOG_PREFIX="[auth]"

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "$LOG_PREFIX Missing required environment variable: $name" >&2
    exit 1
  fi
}

require_env SF_CLIENT_ID
require_env SF_CLIENT_SECRET
require_env SF_LOGIN_URL
require_env SF_ORG_ALIAS

TOKEN_ENDPOINT="${SF_LOGIN_URL%/}/services/oauth2/token"

echo "$LOG_PREFIX Authenticating to Salesforce using OAuth 2.0 client credentials flow"

TOKEN_RESPONSE_FILE="$(mktemp)"
trap 'rm -f "$TOKEN_RESPONSE_FILE"' EXIT

HTTP_STATUS="$(curl -sS -X POST "$TOKEN_ENDPOINT" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SF_CLIENT_ID" \
  -d "client_secret=$SF_CLIENT_SECRET" \
  -w '%{http_code}' \
  -o "$TOKEN_RESPONSE_FILE")"

if [ "$HTTP_STATUS" != "200" ]; then
  echo "$LOG_PREFIX Salesforce authentication request failed with status $HTTP_STATUS" >&2
  cat "$TOKEN_RESPONSE_FILE" >&2 || true
  exit 1
fi

ACCESS_TOKEN="$(python3 - "$TOKEN_RESPONSE_FILE" <<'PY'
import json
import sys
from pathlib import Path
response_path = Path(sys.argv[1])
with response_path.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("access_token", ""))
PY
)"
INSTANCE_URL="$(python3 - "$TOKEN_RESPONSE_FILE" <<'PY'
import json
import sys
from pathlib import Path
response_path = Path(sys.argv[1])
with response_path.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("instance_url", ""))
PY
)"

if [ -z "$ACCESS_TOKEN" ] || [ -z "$INSTANCE_URL" ]; then
  echo "$LOG_PREFIX Unable to parse Salesforce authentication response" >&2
  exit 1
fi

if ! command -v sf >/dev/null 2>&1; then
  echo "$LOG_PREFIX Salesforce CLI not found in PATH" >&2
  exit 1
fi

sf org login access-token --instance-url "$INSTANCE_URL" --access-token "$ACCESS_TOKEN" --alias "$SF_ORG_ALIAS" --set-default >/dev/null

echo "$LOG_PREFIX Salesforce CLI authentication completed"

sf org display --target-org "$SF_ORG_ALIAS" --json > /tmp/sf-org-display.json
python3 - <<'PY'
import json
from pathlib import Path
with Path("/tmp/sf-org-display.json").open("r", encoding="utf-8") as handle:
    payload = json.load(handle)
org_id = payload.get("id") or payload.get("orgId") or payload.get("username")
if not org_id:
    raise SystemExit("Salesforce connectivity check did not return an org identifier")
print(f"{__import__('os').environ.get('LOG_PREFIX')} Salesforce connectivity verified for org: {org_id}")
PY

echo "SF_INSTANCE_URL=$INSTANCE_URL" >> "$GITHUB_ENV"
echo "SF_ORG_ALIAS=$SF_ORG_ALIAS" >> "$GITHUB_ENV"
