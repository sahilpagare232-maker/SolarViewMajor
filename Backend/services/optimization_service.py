"""Deterministic, setback-aware rectangular panel packing."""
from typing import Any
from shapely.geometry import box

from config import settings
from models.area_models import BoundingBox
from models.solar_models import PanelConfig
from services.geojson_service import to_geojson_geometry
from services.pv_service import estimate_panel_annual_energy


def pack_panels(usable_geometry: Any, bounds: BoundingBox, panel: PanelConfig | None = None) -> dict[str, Any]:
    """Place non-overlapping panels on a metric grid wholly covered by the roof."""
    config = panel or PanelConfig(width_m=settings.panel_width_m, length_m=settings.panel_length_m,
                                  rated_power_w=settings.panel_power_w, efficiency=settings.panel_efficiency,
                                  spacing_m=settings.panel_spacing_m, setback_m=settings.roof_setback_m)
    min_x, min_y, max_x, max_y = usable_geometry.bounds
    step_x, step_y = config.width_m + config.spacing_m, config.length_m + config.spacing_m
    features = []
    y = min_y
    while y + config.length_m <= max_y + 1e-9:
        x = min_x
        while x + config.width_m <= max_x + 1e-9:
            panel_poly = box(x, y, x + config.width_m, y + config.length_m)
            if usable_geometry.covers(panel_poly):
                features.append({"type": "Feature", "properties": {"panel_number": len(features) + 1, "rated_power_w": config.rated_power_w}, "geometry": to_geojson_geometry(panel_poly, bounds)})
            x += step_x
        y += step_y
    count = len(features)
    area = round(count * config.width_m * config.length_m, 2)
    energy = estimate_panel_annual_energy((bounds.sw_lat + bounds.ne_lat) / 2, (bounds.sw_lng + bounds.ne_lng) / 2, count, config.rated_power_w)
    return {"panel_count": count, "usable_area_m2": round(usable_geometry.area, 2),
            "panel_covered_area_m2": area, "installed_capacity_kw": round(count * config.rated_power_w / 1000, 2),
            "annual_energy_kwh": energy["annual_energy_kwh_estimate"], "panel_layout": {"type": "FeatureCollection", "features": features},
            "solar_model": energy}
