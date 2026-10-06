from shapely.geometry import Polygon
from models.area_models import BoundingBox
from services.geojson_service import analyze_building, buildings_geojson
from services.osm_service import build_overpass_query, parse_osm_response

BOUNDS = BoundingBox(sw_lat=19, sw_lng=72, ne_lat=19.01, ne_lng=72.01)


def test_geojson_and_metric_area():
    geometry = Polygon([(72, 19), (72.001, 19), (72.001, 19.001), (72, 19.001)])
    building = {"id": "way/1", "tags": {"building": "yes"}, "geometry": geometry}
    result = analyze_building(building, BOUNDS)
    assert result["area_m2"] > 0
    assert result["height"] is None
    geojson = buildings_geojson([building], BOUNDS)
    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"][0]["geometry"]["coordinates"][0][0] == [72.0, 19.0]


def test_overpass_query_includes_way_and_relation():
    query = build_overpass_query(BOUNDS)
    assert 'way["building"]' in query and 'relation["building"]' in query


def test_osm_response_parsing_keeps_valid_footprints():
    parsed = parse_osm_response({"elements": [{"type": "way", "id": 3, "tags": {"building": "yes"}, "geometry": [
        {"lon": 72, "lat": 19}, {"lon": 72.001, "lat": 19},
        {"lon": 72.001, "lat": 19.001}, {"lon": 72, "lat": 19.001},
    ]}, {"type": "way", "id": 4, "geometry": [{"lon": 1, "lat": 1}]}]})
    assert len(parsed) == 1
    assert parsed[0]["id"] == "way/3"
