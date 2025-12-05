#!/usr/bin/env bash

# Manual QA script for the Phone-Address Service.
# Runs a sequence of checks against localhost:8000 using curl and docker/make.

set -u -o pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
REDIS_SERVICE_NAME="redis"
API_SERVICE_NAME="phone-address-api"

info()  { echo -e "\n[INFO] $*"; }
pass()  { echo "[PASS] $*"; }
fail()  { echo "[FAIL] $*"; exit 1; }

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "Required command '$1' not found in PATH"
  fi
}

assert_http() {
  local expected_status="$1"
  local desc="$2"
  shift 2

  local tmp
  tmp="$(mktemp)"
  local status

  if ! status="$(curl -s -o "$tmp" -w "%{http_code}" "$@")"; then
    rm -f "$tmp"
    fail "$desc: curl failed"
  fi

  if [[ "$status" != "$expected_status" ]]; then
    echo "  Response body:"
    cat "$tmp"
    echo
    rm -f "$tmp"
    fail "$desc: expected HTTP $expected_status, got $status"
  fi

  echo "  Status: $status"
  echo "  Body:"
  cat "$tmp"
  echo
  rm -f "$tmp"
}

assert_body_contains() {
  local expected_substring="$1"
  local desc="$2"
  local body="$3"

  if ! grep -q "$expected_substring" <<<"$body"; then
    fail "$desc: expected body to contain '$expected_substring' but got: $body"
  fi
}

###############################################################################
# Prerequisites
###############################################################################

info "Checking prerequisites..."
require_command curl
require_command docker
require_command make

if [[ ! -f "Makefile" || ! -d "src" ]]; then
  fail "Run this script from the project root (Makefile and src/ must exist)."
fi

###############################################################################
# Start the stack (build + up)
###############################################################################

info "Starting stack via 'make up'..."
make up

# Give the containers a brief moment to settle
sleep 2

info "Ensuring Redis DB is clean for QA run..."
docker compose exec "$REDIS_SERVICE_NAME" redis-cli FLUSHDB >/dev/null

###############################################################################
# 1. Infrastructure & Health
###############################################################################

info "1. Infrastructure & Health – Liveness Probe"
assert_http 200 "Health check" "${BASE_URL}/health"

info "1. Infrastructure & Health – Logging Check (manual verification)"
echo "  Last 10 lines of API logs:"
docker logs "$API_SERVICE_NAME" --tail 10 || true
echo "  (Manually verify logs are JSON-structured if desired.)"

###############################################################################
# 2. Validation & Normalization
###############################################################################

info "2. Validation & Normalization – Valid Complex Phone Number"

complex_payload='{"phone": "+1 (555) 000-0001", "address": "Clean Me St"}'
tmp_body="$(mktemp)"
status="$(curl -s -o "$tmp_body" -w "%{http_code}" \
  -H "Content-Type: application/json" \
  -d "$complex_payload" \
  "${BASE_URL}/v1/address")"

if [[ "$status" != "201" ]]; then
  echo "  Body:"
  cat "$tmp_body"
  echo
  rm -f "$tmp_body"
  fail "Valid complex phone: expected 201, got $status"
fi

body="$(cat "$tmp_body")"
rm -f "$tmp_body"
assert_body_contains '"phone":"15550000001"' "Valid complex phone normalization" "$body"
pass "Valid complex phone normalization OK"

info "2. Validation – Phone Too Short (expect 422)"

short_payload='{"phone": "12345", "address": "Short St"}'
assert_http 422 "Phone too short" \
  -H "Content-Type: application/json" \
  -d "$short_payload" \
  "${BASE_URL}/v1/address"

info "2. Validation – Phone Too Long (expect 422)"

long_payload='{"phone": "1234567890123456", "address": "Long St"}'
assert_http 422 "Phone too long" \
  -H "Content-Type: application/json" \
  -d "$long_payload" \
  "${BASE_URL}/v1/address"

###############################################################################
# 3. Core Business Logic (CRUD & Strict REST)
###############################################################################

PHONE_MAIN="9990001"
NON_EXISTENT_PHONE="0000000"
NON_EXISTENT_UPDATE_PHONE="8888888"

info "3A. Creation – Create New Record"
create_payload_main='{"phone": "'"$PHONE_MAIN"'", "address": "Original Address"}'
assert_http 201 "Create new record" \
  -H "Content-Type: application/json" \
  -d "$create_payload_main" \
  "${BASE_URL}/v1/address"

info "3A. Creation – Duplicate Creation (expect 409)"
assert_http 409 "Duplicate create should return 409" \
  -H "Content-Type: application/json" \
  -d "$create_payload_main" \
  "${BASE_URL}/v1/address"

info "3B. Retrieval – Get Existing Record"
tmp_body="$(mktemp)"
status="$(curl -s -o "$tmp_body" -w "%{http_code}" "${BASE_URL}/v1/address/${PHONE_MAIN}")"
if [[ "$status" != "200" ]]; then
  echo "  Body:"
  cat "$tmp_body"
  echo
  rm -f "$tmp_body"
  fail "Get existing record: expected 200, got $status"
fi
body="$(cat "$tmp_body")"
rm -f "$tmp_body"
assert_body_contains '"phone":"'"$PHONE_MAIN"'"' "Get existing phone" "$body"
assert_body_contains '"address":"Original Address"' "Get existing address" "$body"
pass "Get existing record OK"

info "3B. Retrieval – Get Non-Existent Record (expect 404)"
assert_http 404 "Get non-existent record" "${BASE_URL}/v1/address/${NON_EXISTENT_PHONE}"

info "3C. Update – Update Existing Record"
update_payload_main='{"address": "Updated Address"}'
assert_http 200 "Update existing record" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d "$update_payload_main" \
  "${BASE_URL}/v1/address/${PHONE_MAIN}"

info "3C. Update – Verify Update via GET"
tmp_body="$(mktemp)"
status="$(curl -s -o "$tmp_body" -w "%{http_code}" "${BASE_URL}/v1/address/${PHONE_MAIN}")"
if [[ "$status" != "200" ]]; then
  echo "  Body:"
  cat "$tmp_body"
  echo
  rm -f "$tmp_body"
  fail "Verify updated record: expected 200, got $status"
fi
body="$(cat "$tmp_body")"
rm -f "$tmp_body"
assert_body_contains '"address":"Updated Address"' "Updated address" "$body"
pass "Update verification OK"

info "3C. Update – Update Non-Existent Record (expect 404)"
update_payload_ghost='{"address": "Ghost Address"}'
assert_http 404 "Update non-existent record" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d "$update_payload_ghost" \
  "${BASE_URL}/v1/address/${NON_EXISTENT_UPDATE_PHONE}"

info "3C. Update – Update with Missing Body (expect 422)"
assert_http 422 "Update missing body" \
  -X PUT "${BASE_URL}/v1/address/${PHONE_MAIN}"

info "3D. Deletion – Delete Existing Record"
assert_http 204 "Delete existing record" \
  -X DELETE "${BASE_URL}/v1/address/${PHONE_MAIN}"

info "3D. Deletion – Verify Deletion via GET (expect 404)"
assert_http 404 "Verify deletion" "${BASE_URL}/v1/address/${PHONE_MAIN}"

info "3D. Deletion – Delete Non-Existent Record Again (expect 404)"
assert_http 404 "Delete non-existent record" \
  -X DELETE "${BASE_URL}/v1/address/${PHONE_MAIN}"

###############################################################################
# 4. Persistence & Durability (AOF check)
###############################################################################

PERSIST_PHONE="5551112222"

info "4. Persistence – Create Data to Persist"
persist_payload='{"phone": "'"$PERSIST_PHONE"'", "address": "Persist St"}'
assert_http 201 "Create record for persistence check" \
  -H "Content-Type: application/json" \
  -d "$persist_payload" \
  "${BASE_URL}/v1/address"

info "4. Persistence – Restart containers (make down / make up)"
make down
make up

# Give a brief moment after restart
sleep 2

info "4. Persistence – Verify Data Survived Restart"
tmp_body="$(mktemp)"
status="$(curl -s -o "$tmp_body" -w "%{http_code}" "${BASE_URL}/v1/address/${PERSIST_PHONE}")"
if [[ "$status" != "200" ]]; then
  echo "  Body:"
  cat "$tmp_body"
  echo
  rm -f "$tmp_body"
  fail "Persistence check: expected 200, got $status"
fi
body="$(cat "$tmp_body")"
rm -f "$tmp_body"
assert_body_contains '"address":"Persist St"' "Persistence address" "$body"
pass "Persistence & durability check OK"

###############################################################################
# 5. Final Cleanup – Test Suite & Shutdown
###############################################################################

info "5. Final – Run Test Suite via 'make test'"
make test

info "5. Final – Shut Down stack via 'make down'"
make down

pass "Manual QA checklist completed successfully."
