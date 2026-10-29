
import asyncio
import math
import logging
from typing import Any

from shapely.geometry import box

from models.area_models import BoundingBox
from services.osm_service import fetch_buildings, OSMServiceError

logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 1
TARGET_TILE_M = 250
MAX_GRID_TILES = 32
TILE_QUERY_OVERLAP_M = 20
MAX_SUBDIVISION_DEPTH = 1


def split_bounds(bounds: BoundingBox) -> list[BoundingBox]:
    mid_lat = (bounds.sw_lat + bounds.ne_lat) / 2
    mid_lng = (bounds.sw_lng + bounds.ne_lng) / 2

    return [
        BoundingBox(
            sw_lat=bounds.sw_lat, sw_lng=bounds.sw_lng,
            ne_lat=mid_lat, ne_lng=mid_lng,
        ),
        BoundingBox(
            sw_lat=bounds.sw_lat, sw_lng=mid_lng,
            ne_lat=mid_lat, ne_lng=bounds.ne_lng,
        ),
        BoundingBox(
            sw_lat=mid_lat, sw_lng=bounds.sw_lng,
            ne_lat=bounds.ne_lat, ne_lng=mid_lng,
        ),
        BoundingBox(
            sw_lat=mid_lat, sw_lng=mid_lng,
            ne_lat=bounds.ne_lat, ne_lng=bounds.ne_lng,
        ),
    ]


def make_grid(
    bounds: BoundingBox,
    target_tile_m: float = TARGET_TILE_M,
) -> list[BoundingBox]:
    if target_tile_m <= 0:
        raise ValueError("target_tile_m must be greater than zero")

    mid_lat = (bounds.sw_lat + bounds.ne_lat) / 2

    height_m = abs(bounds.ne_lat - bounds.sw_lat) * 111_320
    width_m = (
        abs(bounds.ne_lng - bounds.sw_lng)
        * 111_320
        * math.cos(math.radians(mid_lat))
    )

    rows = max(1, math.ceil(height_m / target_tile_m))
    cols = max(1, math.ceil(width_m / target_tile_m))
    if rows * cols > MAX_GRID_TILES:
        raise OSMServiceError(
            f"Selected area requires {rows * cols} Overpass tiles; "
            f"please select a smaller area (maximum {MAX_GRID_TILES}).",
            status_code=413,
        )

    lat_step = (bounds.ne_lat - bounds.sw_lat) / rows
    lng_step = (bounds.ne_lng - bounds.sw_lng) / cols

    return [
        BoundingBox(
            sw_lat=bounds.sw_lat + r * lat_step,
            sw_lng=bounds.sw_lng + c * lng_step,
            ne_lat=bounds.sw_lat + (r + 1) * lat_step,
            ne_lng=bounds.sw_lng + (c + 1) * lng_step,
        )
        for r in range(rows)
        for c in range(cols)
    ]


def _expanded_tile(bounds: BoundingBox) -> BoundingBox:
    latitude_padding = TILE_QUERY_OVERLAP_M / 111_320
    longitude_scale = max(abs(math.cos(math.radians((bounds.sw_lat + bounds.ne_lat) / 2))), 0.01)
    longitude_padding = TILE_QUERY_OVERLAP_M / (111_320 * longitude_scale)
    return BoundingBox(
        sw_lat=max(-90, bounds.sw_lat - latitude_padding),
        sw_lng=max(-180, bounds.sw_lng - longitude_padding),
        ne_lat=min(90, bounds.ne_lat + latitude_padding),
        ne_lng=min(180, bounds.ne_lng + longitude_padding),
    )


async def fetch_tile_with_fallback(
    bounds: BoundingBox,
    semaphore: asyncio.Semaphore,
    depth: int = 0,
) -> list[dict[str, Any]]:
    try:
        async with semaphore:
            buildings = await fetch_buildings(_expanded_tile(bounds))

        if buildings is None:
            raise OSMServiceError(
                "Tile fetch returned None instead of a building list."
            )

        return buildings

    except OSMServiceError as exc:
        if exc.status_code not in {500, 502, 503, 504}:
            raise

        if depth >= MAX_SUBDIVISION_DEPTH:
            raise

        logger.warning(
            "Splitting failed tile at depth %s; status=%s",
            depth + 1,
            exc.status_code,
        )

        buildings: list[dict[str, Any]] = []
        failures: list[BaseException] = []
        for tile in split_bounds(bounds):
            try:
                buildings.extend(
                    await fetch_tile_with_fallback(tile, semaphore, depth + 1)
                )
            except OSMServiceError as tile_error:
                if tile_error.status_code == 429:
                    raise
                failures.append(tile_error)

        if failures:
            failure_statuses = [
                failure.status_code
                for failure in failures
                if isinstance(failure, OSMServiceError) and failure.status_code is not None
            ]
            status_code = next(
                (status for status in (429, 504, 503, 502) if status in failure_statuses),
                None,
            )
            raise OSMServiceError(
                f"{len(failures)} subdivided tiles failed. {failures[0]}",
                status_code=status_code,
            ) from failures[0]

        return buildings


async def fetch_grid_buildings(
    bounds: BoundingBox,
) -> list[dict[str, Any]]:
    tiles = make_grid(bounds)
    logger.info("Created %s grid tiles", len(tiles))

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    buildings = []
    for tile in tiles:
        buildings.extend(await fetch_tile_with_fallback(tile, semaphore))

    selected_geometry = box(bounds.sw_lng, bounds.sw_lat, bounds.ne_lng, bounds.ne_lat)
    unique = {
        building["id"]: building
        for building in buildings
        if building["geometry"].intersects(selected_geometry)
    }

    logger.info("Retrieved %s unique buildings", len(unique))
    return list(unique.values())