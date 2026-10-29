"""Overpass client and conversion of OSM elements into Shapely footprints."""
import logging
import math
from typing import Any
import httpx
from shapely.errors import GEOSException
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.geometry.base import BaseGeometry

from config import settings
from models.area_models import BoundingBox

logger = logging.getLogger(__name__)



class OSMServiceError(Exception):
    """An upstream Overpass request or response could not be used."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def build_overpass_query(bounds: BoundingBox) -> str:
    """Build an Overpass query for building ways and relations."""
    return f"""
    [out:json][timeout:50];
    (
      way["building"](
        {bounds.sw_lat},{bounds.sw_lng},
        {bounds.ne_lat},{bounds.ne_lng}
      );
      relation["building"](
        {bounds.sw_lat},{bounds.sw_lng},
        {bounds.ne_lat},{bounds.ne_lng}
      );
    );
    out geom;
    """
def _ring_coordinates(points: Any) -> list[tuple[float, float]] | None:
    if not isinstance(points, list) or len(points) < 3:
        return None
    coordinates = []
    for point in points:
        if not isinstance(point, dict) or "lon" not in point or "lat" not in point:
            return None
        longitude, latitude = float(point["lon"]), float(point["lat"])
        if not math.isfinite(longitude) or not math.isfinite(latitude):
            return None
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            return None
        coordinates.append((longitude, latitude))
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    return coordinates if len(coordinates) >= 4 else None


def _valid_polygonal(geometry: BaseGeometry) -> BaseGeometry | None:
    if geometry.is_empty:
        return None
    if not geometry.is_valid:
        geometry = geometry.buffer(0)
    if geometry.is_empty:
        return None
    if geometry.geom_type == "Polygon":
        return geometry
    if geometry.geom_type == "MultiPolygon":
        polygons = [part for part in geometry.geoms if not part.is_empty and part.area > 0]
        if not polygons:
            return None
        merged = unary_union(polygons)
        return merged if merged.is_valid and not merged.is_empty else None
    if geometry.geom_type == "GeometryCollection":
        polygons = [
            part for part in geometry.geoms
            if part.geom_type in {"Polygon", "MultiPolygon"} and not part.is_empty
        ]
        if polygons:
            merged = unary_union(polygons)
            return merged if merged.is_valid and not merged.is_empty else None
    return None


def _relation_geometry(element: dict[str, Any]) -> BaseGeometry | None:
    outer_rings: list[list[tuple[float, float]]] = []
    inner_rings: list[list[tuple[float, float]]] = []
    for member in element.get("members", []):
        if not isinstance(member, dict):
            continue
        role = member.get("role", "outer")
        if role not in {"outer", "inner"}:
            continue
        ring = _ring_coordinates(member.get("geometry"))
        if ring is None:
            continue
        (outer_rings if role == "outer" else inner_rings).append(ring)

    if not outer_rings:
        return None

    outer_polygons = [Polygon(ring) for ring in outer_rings]
    holes: list[list[list[tuple[float, float]]]] = [[] for _ in outer_polygons]
    for inner_ring in inner_rings:
        inner_polygon = Polygon(inner_ring)
        point = inner_polygon.representative_point()
        candidates = [
            (polygon.area, index)
            for index, polygon in enumerate(outer_polygons)
            if polygon.covers(point)
        ]
        if candidates:
            _, index = min(candidates)
            holes[index].append(inner_ring)

    polygons = [
        Polygon(ring, holes[index])
        for index, ring in enumerate(outer_rings)
    ]
    return _valid_polygonal(unary_union(polygons))


def _element_geometry(element: dict[str, Any]) -> BaseGeometry | None:
    if element.get("type") == "relation":
        relation_geometry = _relation_geometry(element)
        if relation_geometry is not None:
            return relation_geometry

    ring = _ring_coordinates(element.get("geometry"))
    if ring is None:
        return None
    return _valid_polygonal(Polygon(ring))



async def fetch_buildings(bounds: BoundingBox) -> list[dict[str, Any]]:
    """Fetch building footprints with status-aware retries and backoff."""
    import asyncio

    query = build_overpass_query(bounds)
    max_attempts = 2

    async with httpx.AsyncClient(
        timeout=settings.request_timeout,
        headers={"User-Agent": "SolarViewMajor/1.0"},
    ) as client:

        for attempt in range(1, max_attempts + 1):
            status_code = None

            try:
                logger.info(
                    "[osm_service] Attempt %s/%s: %s, %s, %s, %s",
                    attempt,
                    max_attempts,
                    bounds.sw_lat,
                    bounds.sw_lng,
                    bounds.ne_lat,
                    bounds.ne_lng,
                )

                response = await client.post(
                    settings.overpass_url,
                    data={"data": query},
                )

                response.raise_for_status()

                payload = response.json()
                buildings = parse_osm_response(payload)

                logger.info(
                    "[osm_service] Parsed %s buildings",
                    len(buildings),
                )
                return buildings

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code

                logger.warning(
                    "Overpass returned HTTP %s on attempt %s/%s",
                    status_code,
                    attempt,
                    max_attempts,
                )

                # A 429 means the server is asking us to reduce requests.
                if status_code == 429:
                    raise OSMServiceError(
                        "Overpass rate-limited the request; please retry later.",
                        status_code=429,
                    ) from exc

                elif status_code == 504 or status_code >= 500:
                    if attempt == max_attempts:
                        break

                    delay = 2 * (2 ** (attempt - 1))

                else:
                    # Do not repeatedly retry ordinary client errors.
                    raise OSMServiceError(
                        f"Overpass returned HTTP {status_code}.",
                        status_code=status_code,
                    ) from exc

            except httpx.TimeoutException as exc:
                logger.warning(
                    "Overpass request timed out on attempt %s/%s",
                    attempt,
                    max_attempts,
                )
                if attempt == max_attempts:
                    raise OSMServiceError(
                        "OpenStreetMap building data request timed out after repeated attempts.",
                        status_code=504,
                    ) from exc
                delay = 2 * (2 ** (attempt - 1))

            except OSMServiceError as exc:
                logger.warning(
                    "Overpass response could not be used on attempt %s/%s: %s",
                    attempt,
                    max_attempts,
                    exc,
                )
                if exc.status_code != 504 or attempt == max_attempts:
                    raise
                delay = 2 * (2 ** (attempt - 1))

            except (httpx.RequestError, ValueError) as exc:
                logger.warning(
                    "Overpass request failed on attempt %s/%s: %s",
                    attempt,
                    max_attempts,
                    exc,
                )

                if attempt == max_attempts:
                    raise OSMServiceError(
                        "OpenStreetMap building data is temporarily "
                        "unavailable after repeated attempts."
                    ) from exc

                delay = 2 * (2 ** (attempt - 1))

            logger.info("Waiting %.1f seconds before retry", delay)
            await asyncio.sleep(delay)

    raise OSMServiceError(
        "Overpass is temporarily unavailable or rate-limiting requests.",
        status_code=status_code,
    )
def parse_osm_response(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse Overpass JSON without making a network request."""
    if not isinstance(payload, dict):
        raise OSMServiceError("OpenStreetMap returned an invalid response.")
    remark = payload.get("remark")
    if remark:
        message = str(remark).lower()
        if "timeout" in message or "timed out" in message:
            raise OSMServiceError(
                "Overpass query timed out while retrieving building data.",
                status_code=504,
            )
        if "rate" in message or "too many" in message:
            raise OSMServiceError(
                "Overpass rate-limited the request; please retry later.",
                status_code=429,
            )
        raise OSMServiceError("OpenStreetMap returned an error while querying buildings.")
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise OSMServiceError("OpenStreetMap returned an invalid response.")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for element in elements:
        if not isinstance(element, dict):
            logger.warning("Skipping malformed OSM element: expected an object.")
            continue
        if element.get("type") not in {"way", "relation"}:
            continue
        element_id = element.get("id")
        if not isinstance(element_id, (int, str)):
            logger.warning("Skipping malformed OSM building with no valid identifier.")
            continue
        osm_id = f"{element.get('type')}/{element_id}"
        if osm_id in seen:
            continue
        try:
            geometry = _element_geometry(element)
        except (GEOSException, KeyError, TypeError, ValueError, OverflowError) as exc:
            logger.warning("Skipping malformed OSM building %s: %s", osm_id, exc)
            continue
        if geometry is not None and not geometry.is_empty:
            seen.add(osm_id)
            tags = element.get("tags", {})
            if not isinstance(tags, dict):
                logger.warning("Ignoring malformed OSM tags for %s.", osm_id)
                tags = {}
            results.append({"id": osm_id, "tags": tags, "geometry": geometry})
    return results