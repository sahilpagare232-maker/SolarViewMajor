"""Deterministic, setback-aware panel packing for projected roof geometry."""
import math
from typing import Any
from shapely.affinity import rotate
from shapely import transform as shapely_transform
from shapely.geometry import Polygon, box, mapping, shape
from shapely.prepared import prep

from config import settings
from models.area_models import BoundingBox
from models.solar_models import PanelConfig
from services.geojson_service import _transformer, metric_crs
from services.pv_service import estimate_panel_annual_energy

MAX_CANDIDATE_POSITIONS = 12_000


def _panel_config(panel: PanelConfig | None) -> PanelConfig:
    config = panel or PanelConfig(width_m=settings.panel_width_m, length_m=settings.panel_length_m,
                                  rated_power_w=settings.panel_power_w, efficiency=settings.panel_efficiency,
                                  spacing_m=settings.panel_spacing_m, setback_m=settings.roof_setback_m)
    return config


def _pack_orientation(usable_geometry: Any, bounds: BoundingBox, config: PanelConfig, angle: float,
                      height_m: float | None) -> list[dict[str, Any]]:
    """Pack a roof in a rotated local frame; prepared covers keeps irregular-roof checks cheap."""
    origin = usable_geometry.centroid
    aligned_roof = rotate(usable_geometry, -angle, origin=origin)
    min_x, min_y, max_x, max_y = aligned_roof.bounds
    step_x = config.width_m + config.spacing_m
    step_y = config.length_m + config.spacing_m
    columns = max(0, math.floor((max_x - min_x - config.width_m) / step_x + 1e-9) + 1)
    rows = max(0, math.floor((max_y - min_y - config.length_m) / step_y + 1e-9) + 1)
    if rows * columns > MAX_CANDIDATE_POSITIONS:
        raise ValueError("This roof produces too many panel candidates. Use a smaller building or increase panel spacing.")
    prepared_roof = prep(aligned_roof)
    to_wgs84 = _transformer(metric_crs(bounds).to_string(), "EPSG:4326")
    features = []
    y = min_y
    while y + config.length_m <= max_y + 1e-8:
        x = min_x
        while x + config.width_m <= max_x + 1e-8:
            panel_poly = box(x, y, x + config.width_m, y + config.length_m)
            if prepared_roof.covers(panel_poly):
                placed = rotate(panel_poly, angle, origin=origin)
                panel_number = len(features) + 1
                features.append({
                    "type": "Feature",
                    "id": f"panel-{panel_number}",
                    "properties": {
                        "panel_id": f"panel-{panel_number}",
                        "panel_number": panel_number,
                        "rated_power_w": config.rated_power_w,
                        "width_m": config.width_m,
                        "length_m": config.length_m,
                        "orientation_deg": angle % 180,
                        "elevation_m": height_m,
                    },
                    "geometry": mapping(shapely_transform(placed, to_wgs84.transform, interleaved=False)),
                })
            x += step_x
        y += step_y
    return features


def pack_panels(usable_geometry: Any, bounds: BoundingBox, panel: PanelConfig | None = None,
                *, height_m: float | None = None, setback_already_applied: bool = False,
                latitude: float | None = None, longitude: float | None = None) -> dict[str, Any]:
    """Choose the better of two deterministic grid orientations, maximizing feasible panel count.

    Input geometry must be in a local metric CRS. The objective is panel count, with
    coverage as the tie-breaker; it is a geometric heuristic, not a global optimum.
    """
    config = _panel_config(panel)
    usable_geometry = usable_geometry if setback_already_applied else usable_geometry.buffer(-config.setback_m)
    if usable_geometry.is_empty or usable_geometry.area <= 0:
        usable_area = 0.0
        layouts = [[], []]
    else:
        layouts = [
            _pack_orientation(usable_geometry, bounds, config, 0, height_m),
            _pack_orientation(usable_geometry, bounds, config, 90, height_m),
        ]
        usable_area = usable_geometry.area
    features = max(layouts, key=lambda layout: (len(layout), len(layout) * config.width_m * config.length_m))
    count = len(features)
    area = round(count * config.width_m * config.length_m, 2)
    latitude = latitude if latitude is not None else (bounds.sw_lat + bounds.ne_lat) / 2
    longitude = longitude if longitude is not None else (bounds.sw_lng + bounds.ne_lng) / 2
    energy = estimate_panel_annual_energy(latitude, longitude, count, config.rated_power_w)
    return {"panel_count": count, "usable_area_m2": round(usable_area, 2),
            "panel_covered_area_m2": area, "installed_capacity_kw": round(count * config.rated_power_w / 1000, 2),
            "annual_energy_kwh": energy["annual_energy_kwh_estimate"], "panel_layout": {"type": "FeatureCollection", "features": features},
            "solar_model": energy, "placement_orientation_deg": features[0]["properties"]["orientation_deg"] if features else None,
            "panel_spec": {"width_m": config.width_m, "length_m": config.length_m, "rated_power_w": config.rated_power_w,
                           "spacing_m": config.spacing_m, "setback_m": config.setback_m},
            "optimization_objective": "maximize feasible panel count; use covered area as tie-breaker",
            "optimizer": "deterministic geometric grid heuristic"}


def optimize_building(building_id: str, geometry_geojson: dict[str, Any], bounds: BoundingBox,
                      panel: PanelConfig | None = None, height_m: float | None = None) -> dict[str, Any]:
    """Project and optimize one selected WGS84 polygon/multipolygon footprint."""
    try:
        geometry = shape(geometry_geojson)
    except (TypeError, ValueError) as exc:
        raise ValueError("Building geometry is invalid GeoJSON.") from exc
    if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty:
        raise ValueError("Building geometry must be a non-empty Polygon or MultiPolygon.")
    min_lon, min_lat, max_lon, max_lat = geometry.bounds
    if not all(math.isfinite(value) for value in geometry.bounds) or min_lon < -180 or max_lon > 180 or min_lat < -90 or max_lat > 90:
        raise ValueError("Building coordinates must be valid longitude/latitude values.")
    if not geometry.is_valid:
        geometry = geometry.buffer(0)
    if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"} or not geometry.is_valid:
        raise ValueError("Building geometry could not be repaired into a valid polygon.")

    from services.geojson_service import _project

    projected = _project(geometry, bounds)
    config = _panel_config(panel)
    roof = projected.buffer(-config.setback_m)
    if roof.is_empty:
        roof = Polygon()
    centroid = geometry.centroid
    result = pack_panels(
        roof,
        bounds,
        config,
        height_m=height_m,
        setback_already_applied=True,
        latitude=centroid.y,
        longitude=centroid.x,
    )
    result.update({
        "building_id": building_id,
        "footprint_area_m2": round(projected.area, 2),
        "roof_assumption": "flat roof approximated from the OSM building footprint; pitch, obstacles and shading are not modeled",
        "roof_geometry_source": "OpenStreetMap footprint",
        "roof_height_m": height_m,
        "roof_height_source": "OpenStreetMap height tag; treated as building-top elevation above local ground" if height_m is not None else None,
        "annual_energy_data_class": result["solar_model"]["energy_data_class"],
        "panel_coverage_percent": round(100 * result["panel_covered_area_m2"] / result["usable_area_m2"], 1) if result["usable_area_m2"] else 0,
    })
    return result
