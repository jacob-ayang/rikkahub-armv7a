#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/ci/prepare-secrets.sh <keystore_path> <signing_config_path> <google_services_json_path>

Example:
  scripts/ci/prepare-secrets.sh \
    ./rikkahub.keystore \
    ./ci/signing.properties \
    ./app/google-services.json

Output:
  KEY_BASE64=<...>
  SIGNING_CONFIG_B64=<...>
  GOOGLE_SERVICES_JSON_B64=<...>

Notes:
  - The script only prints Base64 values to stdout and does not write files.
  - Handle terminal history carefully, because outputs contain secrets.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -ne 3 ]; then
  usage
  exit 1
fi

KEYSTORE_PATH="$1"
SIGNING_CONFIG_PATH="$2"
GOOGLE_SERVICES_PATH="$3"

for path in "$KEYSTORE_PATH" "$SIGNING_CONFIG_PATH" "$GOOGLE_SERVICES_PATH"; do
  if [ ! -f "$path" ]; then
    echo "ERROR: File not found: $path" >&2
    exit 1
  fi
done

to_base64_single_line() {
  local input_file="$1"
  if base64 --help 2>/dev/null | grep -q -- "-w"; then
    base64 -w 0 "$input_file"
  else
    base64 "$input_file" | tr -d '\n'
  fi
}

echo "KEY_BASE64=$(to_base64_single_line "$KEYSTORE_PATH")"
echo "SIGNING_CONFIG_B64=$(to_base64_single_line "$SIGNING_CONFIG_PATH")"
echo "GOOGLE_SERVICES_JSON_B64=$(to_base64_single_line "$GOOGLE_SERVICES_PATH")"
