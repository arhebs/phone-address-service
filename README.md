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

All phone inputs (body and path) are normalized by a shared helper:

- Strip all non-digit characters.
- Require **7–15 digits** (inclusive).
    - Example: `+1 (555) 123-4567` → `15551234567`.
    - Example: `123-4567` → `1234567`.
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

## Example Requests

Create a mapping:

```bash
curl -X POST http://localhost:8000/v1/address \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1 (555) 123-4567", "address": "123 Main St"}'
```

Get a mapping:

```bash
curl http://localhost:8000/v1/address/+1%20(555)%20123-4567
```

Update a mapping:

```bash
curl -X PUT http://localhost:8000/v1/address/15551234567 \
  -H "Content-Type: application/json" \
  -d '{"address": "456 Elm St"}'
```

Delete a mapping:

```bash
curl -X DELETE http://localhost:8000/v1/address/15551234567
```

Health check:

```bash
curl http://localhost:8000/health
```
