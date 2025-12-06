"""Integration tests for the phone-address API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_and_get_address(async_client: AsyncClient) -> None:
    payload = {"phone": "+1 (202) 555-0001", "address": "123 Main St"}

    # Create
    create_resp = await async_client.post("/v1/address", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["phone"] == "+12025550001"
    assert data["address"] == "123 Main St"

    # Get
    get_resp = await async_client.get(f"/v1/address/{payload['phone']}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data == data


@pytest.mark.asyncio
async def test_create_duplicate_returns_conflict(async_client: AsyncClient) -> None:
    payload = {"phone": "+12025550002", "address": "Addr"}

    first = await async_client.post("/v1/address", json=payload)
    assert first.status_code == 201

    second = await async_client.post("/v1/address", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_get_missing_returns_not_found(async_client: AsyncClient) -> None:
    resp = await async_client.get("/v1/address/+12025550003")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_existing_address(async_client: AsyncClient) -> None:
    payload = {"phone": "+12025550004", "address": "Old Address"}
    create_resp = await async_client.post("/v1/address", json=payload)
    assert create_resp.status_code == 201
    phone_normalized = create_resp.json()["phone"]

    update_resp = await async_client.put(
        f"/v1/address/{phone_normalized}", json={"address": "New Address"}
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["phone"] == phone_normalized
    assert data["address"] == "New Address"


@pytest.mark.asyncio
async def test_update_missing_returns_not_found(async_client: AsyncClient) -> None:
    resp = await async_client.put(
        "/v1/address/+12025550005", json={"address": "New Address"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_existing_address(async_client: AsyncClient) -> None:
    payload = {"phone": "+12025550006", "address": "Somewhere"}
    create_resp = await async_client.post("/v1/address", json=payload)
    assert create_resp.status_code == 201
    phone_normalized = create_resp.json()["phone"]

    delete_resp = await async_client.delete(f"/v1/address/{phone_normalized}")
    assert delete_resp.status_code == 204

    get_resp = await async_client.get(f"/v1/address/{phone_normalized}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_missing_returns_not_found(async_client: AsyncClient) -> None:
    resp = await async_client.delete("/v1/address/+12025550007")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_phone_validation(async_client: AsyncClient) -> None:
    # Too short phone number
    resp = await async_client.post(
        "/v1/address", json={"phone": "123456", "address": "Addr"}
    )
    assert resp.status_code == 422
