from shapely.geometry import box
from models.area_models import BoundingBox
from models.solar_models import PanelConfig
from services.optimization_service import pack_panels


def test_panel_packing_is_inside_roof_and_non_overlapping():
    bounds = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.01, ne_lng=72.01)
    config = PanelConfig(width_m=1, length_m=2, spacing_m=0, setback_m=0, rated_power_w=400)
    roof = box(0, 0, 3, 4)
    result = pack_panels(roof, bounds, config)
    assert result["panel_count"] == 6
    assert result["installed_capacity_kw"] == 2.4
    assert result["panel_layout"]["type"] == "FeatureCollection"
