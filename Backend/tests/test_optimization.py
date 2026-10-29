import math

import pytest
from shapely.geometry import Point, Polygon, box, shape
from models.area_models import BoundingBox
from models.solar_models import PanelConfig
from services.geojson_service import _project, to_geojson_geometry
from services.optimization_service import optimize_building, pack_panels


def test_panel_packing_is_inside_roof_and_non_overlapping():
    bounds = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.01, ne_lng=72.01)
    config = PanelConfig(width_m=1, length_m=2, spacing_m=0, setback_m=0, rated_power_w=400)
    roof = box(0, 0, 3, 4)
    result = pack_panels(roof, bounds, config)
    assert result["panel_count"] == 6
    assert result["installed_capacity_kw"] == 2.4
    assert result["panel_layout"]["type"] == "FeatureCollection"


def _footprint_meters(width, height, latitude=19.0, longitude=72.0):
    bounds = BoundingBox(sw_lat=18.99, sw_lng=71.99, ne_lat=19.02, ne_lng=72.02)
    origin_x, origin_y = _project(Point(longitude, latitude), bounds).coords[0]
    return shape(to_geojson_geometry(box(origin_x, origin_y, origin_x + width, origin_y + height), bounds))


def _optimize(footprint, panel, height_m=8):
    bounds = BoundingBox(sw_lat=18.99, sw_lng=71.99, ne_lat=19.02, ne_lng=72.02)
    result = optimize_building("way/123", footprint.__geo_interface__, bounds, panel, height_m)
    return result, bounds


def test_selected_rectangular_roof_reports_count_capacity_and_height():
    roof = _footprint_meters(8, 8)
    config = PanelConfig(width_m=1, length_m=2, rated_power_w=400, spacing_m=0, setback_m=0)
    result, _ = _optimize(roof, config)

    assert result["panel_count"] > 0
    assert result["installed_capacity_kw"] == round(result["panel_count"] * 0.4, 2)
    assert result["roof_height_m"] == 8
    assert result["optimizer"] == "deterministic geometric grid heuristic"
    assert result["panel_layout"]["features"][0]["properties"]["elevation_m"] == 8


def test_irregular_roof_panels_stay_inside_and_do_not_overlap():
    latitude, longitude = 19.0, 72.0
    scale_x = 1 / (111_320 * math.cos(math.radians(latitude)))
    scale_y = 1 / 110_540
    outline = [
        (longitude, latitude),
        (longitude + 12 * scale_x, latitude),
        (longitude + 12 * scale_x, latitude + 4 * scale_y),
        (longitude + 6 * scale_x, latitude + 4 * scale_y),
        (longitude + 6 * scale_x, latitude + 12 * scale_y),
        (longitude, latitude + 12 * scale_y),
        (longitude, latitude),
    ]
    roof = Polygon(outline)
    config = PanelConfig(width_m=1, length_m=2, rated_power_w=400, spacing_m=0.1, setback_m=0.3)
    result, bounds = _optimize(roof, config)

    projected_roof = _project(roof, bounds).buffer(-config.setback_m)
    panels = [_project(shape(feature["geometry"]), bounds) for feature in result["panel_layout"]["features"]]
    assert result["panel_count"] > 0
    assert all(projected_roof.buffer(1e-5).covers(panel) for panel in panels)
    assert all(a.intersection(b).area < 1e-6 for i, a in enumerate(panels) for b in panels[i + 1:])


def test_small_roof_returns_empty_layout_without_fabricated_panels():
    roof = _footprint_meters(1, 1)
    config = PanelConfig(width_m=1.1, length_m=1.8, spacing_m=0.05, setback_m=0.2)
    result, _ = _optimize(roof, config, height_m=None)

    assert result["panel_count"] == 0
    assert result["installed_capacity_kw"] == 0
    assert result["annual_energy_kwh"] == 0
    assert result["roof_height_m"] is None


def test_invalid_non_polygon_building_geometry_is_rejected():
    point = {"type": "Point", "coordinates": [72, 19]}
    bounds = BoundingBox(sw_lat=18.99, sw_lng=71.99, ne_lat=19.02, ne_lng=72.02)

    with pytest.raises(ValueError, match="Polygon or MultiPolygon"):
        optimize_building("node/123", point, bounds)


def test_candidate_limit_prevents_pathological_runtime():
    bounds = BoundingBox(sw_lat=18.99, sw_lng=71.99, ne_lat=19.02, ne_lng=72.02)
    large_roof = box(0, 0, 10_000, 10_000)
    config = PanelConfig(width_m=1, length_m=2, spacing_m=0, setback_m=0)

    with pytest.raises(ValueError, match="too many panel candidates"):
        pack_panels(large_roof, bounds, config, setback_already_applied=True)
