"""Integration tests for the FastAPI REST API."""

import pytest
from httpx import AsyncClient, ASGITransport
from laaf.api.server import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["techniques_loaded"] == 49


@pytest.mark.asyncio
async def test_list_techniques(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/techniques")
    assert r.status_code == 200
    techniques = r.json()
    assert len(techniques) == 49


@pytest.mark.asyncio
async def test_get_technique(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/techniques/E1")
    assert r.status_code == 200
    assert r.json()["id"] == "E1"


@pytest.mark.asyncio
async def test_technique_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/techniques/NONEXISTENT")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_and_get_scan(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create scan
        r = await client.post("/scans", json={
            "target": "mock",
            "stages": ["S1"],
            "max_payloads": 5,
            "rate_delay": 0.1,
        })
        assert r.status_code == 202
        scan = r.json()
        scan_id = scan["scan_id"]
        assert scan["status"] == "running"

        # Get scan
        r2 = await client.get(f"/scans/{scan_id}")
        assert r2.status_code == 200


@pytest.mark.asyncio
async def test_list_scans(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/scans")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
