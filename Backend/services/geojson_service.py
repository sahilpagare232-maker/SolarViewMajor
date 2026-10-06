"""GeoJSON conversion and metric building geometry analysis."""
from typing import Any
from pyproj import CRS, Transformer
from shapely.geometry import mapping
from shapely.ops import transform

from config import settings
from models.area_models import BoundingBox


def metric_crs(bounds: BoundingBox) -> CRS:
    """Select a local UTM projection suitable for metric area calculations."""
    lon = (bounds.sw_lng + bounds.ne_lng) / 2
    lat = (bounds.sw_lat + bounds.ne_lat) / 2
    zone = max(1, min(60, int((lon + 180) // 6) + 1))
    return CRS.from_epsg((32600 if lat >= 0 else 32700) + zone)


def _project(geometry: Any, bounds: BoundingBox, inverse: bool = False) -> Any:
    target = metric_crs(bounds)
    transformer = Transformer.from_crs(target if inverse else "EPSG:4326", "EPSG:4326" if inverse else target, always_xy=True)
    return transform(transformer.transform, geometry)


def analyze_building(building: dict[str, Any], bounds: BoundingBox) -> dict[str, Any]:
    """Calculate footprint area and centroid in a local metric projection."""
    geometry = building["geometry"]
    projected = _project(geometry, bounds)
    centroid = geometry.centroid
    min_rect = projected.minimum_rotated_rectangle
    coords = list(min_rect.exterior.coords) if hasattr(min_rect, "exterior") else []
    orientation = None
    if len(coords) > 1:
        import math
        dx, dy = coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]
        orientation = round(math.degrees(math.atan2(dy, dx)) % 180, 2)
    tags = building.get("tags", {})
    try:
        height = float(tags["height"].removesuffix(" m")) if tags.get("height") else None
    except (ValueError, AttributeError):
        height = None
    return {"building_id": building["id"], "building_type": tags.get("building"), "height": height,
            "area_m2": round(projected.area, 2), "centroid": {"lat": centroid.y, "lng": centroid.x},
            "orientation_deg": orientation, "geometry": mapping(geometry), "_projected": projected}


def buildings_geojson(buildings: list[dict[str, Any]], bounds: BoundingBox) -> dict[str, Any]:
    """Build frontend-ready building features with metric area and honest height."""
    features = []
    for item in buildings:
        row = analyze_building(item, bounds)
        features.append({"type": "Feature", "id": row["building_id"], "properties": {k: row[k] for k in ("building_id", "building_type", "height", "area_m2", "centroid", "orientation_deg")}, "geometry": row["geometry"]})
    return {"type": "FeatureCollection", "features": features}


def usable_roof(geometry: Any, bounds: BoundingBox, setback_m: float | None = None) -> Any:
    """Approximate usable roof as footprint interior after configurable setback."""
    projected = _project(geometry, bounds)
    roof = projected.buffer(-(settings.roof_setback_m if setback_m is None else setback_m))
    return roof


def to_geojson_geometry(projected_geometry: Any, bounds: BoundingBox) -> dict[str, Any]:
    """Transform a local metric geometry back to GeoJSON longitude/latitude."""
    return mapping(_project(projected_geometry, bounds, inverse=True))
