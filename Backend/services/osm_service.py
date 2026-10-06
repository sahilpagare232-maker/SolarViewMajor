"""Overpass client and conversion of OSM elements into Shapely footprints."""
import logging
from typing import Any
import httpx
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from config import settings
from models.area_models import BoundingBox

logger = logging.getLogger(__name__)


class OSMServiceError(Exception):
    """An upstream Overpass request or response could not be used."""


def build_overpass_query(bounds: BoundingBox) -> str:
    """Build an Overpass query for building ways and relations in the bounds."""
    return f"[out:json][timeout:50];(way[\"building\"]({bounds.sw_lat},{bounds.sw_lng},{bounds.ne_lat},{bounds.ne_lng});relation[\"building\"]({bounds.sw_lat},{bounds.sw_lng},{bounds.ne_lat},{bounds.ne_lng}););out body geom;"


def _element_geometry(element: dict[str, Any]) -> BaseGeometry | None:
    geom = element.get("geometry")
    if geom and len(geom) >= 3:
        coords = [(float(p["lon"]), float(p["lat"])) for p in geom if "lon" in p and "lat" in p]
        if len(coords) >= 3:
            polygon = Polygon(coords)
            return polygon if polygon.is_valid else polygon.buffer(0)
    if element.get("type") == "relation":
        outer_rings: list[list[tuple[float, float]]] = []
        for member in element.get("members", []):
            if member.get("role", "outer") != "outer":
                continue
            points = member.get("geometry", [])
            coords = [(float(p["lon"]), float(p["lat"])) for p in points if "lon" in p and "lat" in p]
            if len(coords) >= 4:
                outer_rings.append(coords)
        if outer_rings:
            polygons = [Polygon(ring) for ring in outer_rings]
            from shapely.geometry import MultiPolygon
            result = MultiPolygon([p if p.is_valid else p.buffer(0) for p in polygons])
            return result if result.is_valid else result.buffer(0)
    return None


async def fetch_buildings(bounds: BoundingBox) -> list[dict[str, Any]]:
    """Fetch OSM building footprints; never substitute fabricated data."""
    query = build_overpass_query(bounds)
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(settings.overpass_url, data={"data": query}, headers={"User-Agent": "SolarViewMajor/1.0"})
        if response.status_code == 504:
            raise OSMServiceError("OpenStreetMap Overpass timed out (HTTP 504). Try a smaller selected area.")
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as exc:
        raise OSMServiceError("OpenStreetMap Overpass request timed out. Try a smaller selected area.") from exc
    except OSMServiceError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Overpass request failed: %s", exc)
        raise OSMServiceError("OpenStreetMap building data is temporarily unavailable.") from exc
    return parse_osm_response(payload)


def parse_osm_response(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse Overpass JSON without making a network request."""
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise OSMServiceError("OpenStreetMap returned an invalid response.")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for element in elements:
        if element.get("type") not in {"way", "relation"}:
            continue
        osm_id = f"{element.get('type')}/{element.get('id')}"
        if osm_id in seen:
            continue
        geometry = _element_geometry(element)
        if geometry is not None and not geometry.is_empty:
            seen.add(osm_id)
            results.append({"id": osm_id, "tags": element.get("tags", {}), "geometry": geometry})
    return results
