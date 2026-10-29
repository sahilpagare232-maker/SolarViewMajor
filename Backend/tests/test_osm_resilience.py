import asyncio

import httpx
import pytest

from models.area_models import BoundingBox
from services import osm_service
from services.osm_service import OSMServiceError


BOUNDS = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.001, ne_lng=72.001)


def use_mock_transport(monkeypatch, handler):
    async_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)

    def create_client(*args, **kwargs):
        return async_client(*args, transport=transport, **kwargs)

    monkeypatch.setattr(osm_service.httpx, "AsyncClient", create_client)


def test_rate_limit_is_reported_without_retrying(monkeypatch):
    request_count = 0

    def handler(request):
        nonlocal request_count
        request_count += 1
        return httpx.Response(429, headers={"Retry-After": "30"})

    use_mock_transport(monkeypatch, handler)

    with pytest.raises(OSMServiceError, match="rate-limited") as error:
        asyncio.run(osm_service.fetch_buildings(BOUNDS))

    assert error.value.status_code == 429
    assert request_count == 1


def test_timeout_is_retried_once_and_returned_as_gateway_timeout(monkeypatch):
    request_count = 0

    def handler(request):
        nonlocal request_count
        request_count += 1
        raise httpx.ReadTimeout("read timed out", request=request)

    async def skip_backoff(_delay):
        return None

    use_mock_transport(monkeypatch, handler)
    monkeypatch.setattr(asyncio, "sleep", skip_backoff)

    with pytest.raises(OSMServiceError, match="timed out") as error:
        asyncio.run(osm_service.fetch_buildings(BOUNDS))

    assert error.value.status_code == 504
    assert request_count == 2


def test_overpass_timeout_remark_is_retried_and_returned_as_gateway_timeout(monkeypatch):
    request_count = 0

    def handler(_request):
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={"remark": "runtime error: Query timed out", "elements": []},
        )

    async def skip_backoff(_delay):
        return None

    use_mock_transport(monkeypatch, handler)
    monkeypatch.setattr(asyncio, "sleep", skip_backoff)

    with pytest.raises(OSMServiceError, match="timed out") as error:
        asyncio.run(osm_service.fetch_buildings(BOUNDS))

    assert error.value.status_code == 504
    assert request_count == 2
