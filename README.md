# Phone-Address Service

Phone-to-address directory microservice built with **FastAPI** and **Redis**.
It exposes a small, strict REST API for managing phone → address mappings with
atomic Redis operations and full async support.

---

## Overview

- **Purpose**: Low-latency lookup and storage of addresses keyed by phone number.
- **Stack**: Python 3.10+, FastAPI, `redis.asyncio`, Pydantic v2, Docker, docker-compose.
- **Storage**: Redis with keys `address:{normalized_phone}` and JSON values `{"address": "..."}`.
- **Semantics**:
    - `POST` is **create-only** (409 on conflict, no upsert).
    - `PUT` is **update-only** (404 if the record does not exist).
    - All writes are atomic via Redis primitives (`SET NX`, `SET XX`, `DEL`).

---

## API Summary

Base path: `/`

- `GET /v1/address/{phone}`
    - Normalize `{phone}` before lookup.
    - **200**: `{"phone": "<normalized>", "address": "<address>"}` if found.
    - **404**: If not found.

- `POST /v1/address`
    - Body: `{"phone": "string", "address": "string"}`
    - Uses `SET ... NX` (create if not exists).
    - **201**: Created successfully.
    - **409**: Record for that phone already exists (no upsert).

- `PUT /v1/address/{phone}`
    - Body: `{"address": "string"}`
    - Uses `SET ... XX` (update if exists).
    - **200**: Updated successfully.
    - **404**: Record not found.

- `DELETE /v1/address/{phone}`
    - Uses `DEL key`.
    - **204**: Record deleted (Redis returned 1).
    - **404**: Record not found (Redis returned 0).

- `GET /health`
    - Liveness-only endpoint.
    - **200** with `{"status": "ok"}`.
    - Does **not** touch Redis.

---

## Phone Normalization & Validation

All phone inputs (body and path) are normalized by a shared helper that uses
Google's libphonenumber (`phonenumbers` package) to:

- Parse the phone number (using **US** as the default region when no country
  code is provided, while still supporting fully-qualified international
  numbers starting with `+`).
- Validate the parsed number using libphonenumber's rules.
- Format the number into **E.164** format, e.g.:
    - `+1 (202) 555-0001` → `+12025550001`.
- If invalid, validation fails and FastAPI returns **422 Unprocessable Entity**.

Normalization is implemented in:

- `src/core/utils.py`: `normalize_phone(phone: str) -> str`
- Pydantic models in `src/models/schemas.py`:
    - `AddressCreate.phone`
    - `PhonePathParam.phone`

---

## Running with Docker

Prerequisites:

- Docker
- docker-compose
- GNU Make (for the provided shortcuts)

Configuration:

- The application expects the following environment variables (or a `.env` file)
  for Redis configuration:
    - `APP_REDIS_HOST` (**required**)
    - `APP_REDIS_PORT` (default: `6379`)
    - `APP_REDIS_DB` (default: `0`)
- In Docker, these are set via `docker-compose.yml` (e.g. `APP_REDIS_HOST=redis`).
- For local development and tests, you can create a `.env` file in the project
  root, for example:

  ```env
  APP_REDIS_HOST=localhost
  APP_REDIS_PORT=6379
  APP_REDIS_DB=0
  ```

Commands:

- **Build and start** the stack (API + Redis):

  ```bash
  make up
  ```

  This runs `docker compose up --build -d`, rebuilding images as needed.

- **Stop** all containers:

  ```bash
  make down
  ```

- **Run tests inside Docker**:

  ```bash
  make test
  ```

  This runs `pytest -q` inside the `api` container, using the same image and config
  as production. Redis is cleaned before and after each test.

- **Lint** the codebase (locally, not in Docker):

  ```bash
  make lint
  ```

- To run only the **unit tests** (e.g., the service layer tests that do not
  require a running Redis instance), you can run:

  ```bash
  pytest tests/unit
  ```

---

## Development Notes

- The FastAPI app lives in `src/main.py` and uses a **lifespan** context manager to:
    - Configure JSON logging.
    - Initialize a single async Redis client and attach it to `app.state.redis`.
    - Close the client gracefully on shutdown.

- Service logic is encapsulated in `src/services/address_service.py`:
    - Uses `SET NX` / `SET XX` / `DEL` for atomic create/update/delete.
    - Raises domain exceptions:
        - `EntityAlreadyExists` → mapped to **409 Conflict**.
        - `EntityNotFound` → mapped to **404 Not Found**.

- Pydantic models and validators are in `src/models/schemas.py`.
- API routes are defined under `src/api/`:
    - Health: `src/api/health.py`
    - Address endpoints: `src/api/v1/endpoints/address.py`

---

## QA & Verification

- Run the automated integration tests:

  ```bash
  make test
  ```

- Run the full manual QA checklist script (wraps the behavior described above):

  ```bash
  ./qa_manual.sh
  ```

  This script will:
    - Build and start the stack.
    - Exercise all endpoints via `curl`.
    - Verify strict REST semantics and Redis persistence across restarts.
    - Run `make test`.
    - Tear down the stack at the end.

---

## Example Requests

Create a mapping:

```bash
curl -X POST http://localhost:8000/v1/address \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1 (202) 555-0001", "address": "123 Main St"}'
```

Get a mapping:

```bash
curl http://localhost:8000/v1/address/+1%20(202)%20555-0001
```

Update a mapping:

```bash
curl -X PUT http://localhost:8000/v1/address/+12025550001 \
  -H "Content-Type: application/json" \
  -d '{"address": "456 Elm St"}'
```

Delete a mapping:

```bash
curl -X DELETE http://localhost:8000/v1/address/+12025550001
```

Health check:

```bash
curl http://localhost:8000/health
```
