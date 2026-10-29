import asyncio

import pytest
from shapely.geometry import Polygon

from models.area_models import BoundingBox
from services import grid_service
from services.osm_service import OSMServiceError


def test_grid_tiles_cover_bounds_without_gaps():
    bounds = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.004, ne_lng=72.004)
    tiles = grid_service.make_grid(bounds)

    assert len(tiles) == 4
    assert min(tile.sw_lat for tile in tiles) == bounds.sw_lat
    assert max(tile.ne_lat for tile in tiles) == bounds.ne_lat
    assert min(tile.sw_lng for tile in tiles) == bounds.sw_lng
    assert max(tile.ne_lng for tile in tiles) == bounds.ne_lng
    for tile in tiles:
        assert tile.sw_lat < tile.ne_lat
        assert tile.sw_lng < tile.ne_lng


def test_grid_fetches_overlapping_tiles_and_deduplicates_intersecting_buildings(monkeypatch):
    bounds = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.004, ne_lng=72.004)
    building = {
        "id": "way/1",
        "tags": {"building": "yes", "height": "9"},
        "geometry": Polygon([
            (72.001, 19.001),
            (72.002, 19.001),
            (72.002, 19.002),
            (72.001, 19.002),
        ]),
    }
    outside = {
        "id": "way/outside",
        "tags": {"building": "yes"},
        "geometry": Polygon([
            (72.02, 19.02),
            (72.021, 19.02),
            (72.021, 19.021),
            (72.02, 19.021),
        ]),
    }
    queried_bounds = []

    async def mocked_fetch(tile):
        queried_bounds.append(tile)
        return [building, outside]

    monkeypatch.setattr(grid_service, "fetch_buildings", mocked_fetch)
    result = asyncio.run(grid_service.fetch_grid_buildings(bounds))

    assert len(queried_bounds) == 4
    assert queried_bounds[0].sw_lat < bounds.sw_lat
    assert queried_bounds[-1].ne_lat > bounds.ne_lat
    assert queried_bounds[0].ne_lat > queried_bounds[2].sw_lat
    assert queried_bounds[0].ne_lng > queried_bounds[1].sw_lng
    assert [item["id"] for item in result] == ["way/1"]
    assert result[0]["tags"]["height"] == "9"


def test_grid_propagates_rate_limit_instead_of_returning_partial_data(monkeypatch):
    bounds = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.004, ne_lng=72.004)
    calls = 0

    async def rate_limited(_tile):
        nonlocal calls
        calls += 1
        raise OSMServiceError("Overpass rate-limited the request.", status_code=429)

    monkeypatch.setattr(grid_service, "fetch_buildings", rate_limited)

    with pytest.raises(OSMServiceError, match="rate-limited") as error:
        asyncio.run(grid_service.fetch_grid_buildings(bounds))

    assert error.value.status_code == 429
    assert calls == 1


def test_large_area_is_rejected_before_creating_too_many_tiles():
    bounds = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.1, ne_lng=72.1)

    with pytest.raises(OSMServiceError, match="select a smaller area") as error:
        grid_service.make_grid(bounds)

    assert error.value.status_code == 413
