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
    assert list(geojson["features"][0]["geometry"]["coordinates"][0][0]) == [72.0, 19.0]


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


def test_height_tag_is_normalized_and_preserved():
    geometry = Polygon([(72, 19), (72.001, 19), (72.001, 19.001), (72, 19.001)])
    building = {
        "id": "way/height",
        "tags": {"building": "yes", "height": "12.5m"},
        "geometry": geometry,
    }

    result = analyze_building(building, BOUNDS)
    feature = buildings_geojson([building], BOUNDS)["features"][0]

    assert result["height"] == 12.5
    assert feature["properties"]["height"] == 12.5
    assert feature["properties"]["height_tag"] == "12.5m"


def test_relation_multipolygon_keeps_outer_rings_and_inner_hole():
    def ring(west, south, east, north):
        return [
            {"lon": west, "lat": south},
            {"lon": east, "lat": south},
            {"lon": east, "lat": north},
            {"lon": west, "lat": north},
            {"lon": west, "lat": south},
        ]

    parsed = parse_osm_response({
        "elements": [{
            "type": "relation",
            "id": 20,
            "tags": {"building": "yes", "height": "8 m"},
            "members": [
                {"role": "outer", "geometry": ring(72, 19, 72.01, 19.01)},
                {"role": "inner", "geometry": ring(72.002, 19.002, 72.004, 19.004)},
                {"role": "outer", "geometry": ring(72.02, 19.02, 72.03, 19.03)},
            ],
        }],
    })

    geometry = parsed[0]["geometry"]
    assert geometry.geom_type == "MultiPolygon"
    assert len(geometry.geoms) == 2
    assert sum(len(polygon.interiors) for polygon in geometry.geoms) == 1


def test_malformed_building_geometry_is_skipped_without_losing_valid_building():
    parsed = parse_osm_response({
        "elements": [
            {
                "type": "way",
                "id": 30,
                "geometry": [
                    {"lon": "not-a-number", "lat": 19},
                    {"lon": 72.001, "lat": 19},
                    {"lon": 72.001, "lat": 19.001},
                ],
            },
            {
                "type": "way",
                "id": 31,
                "tags": {"building": "yes"},
                "geometry": [
                    {"lon": 72, "lat": 19},
                    {"lon": 72.001, "lat": 19},
                    {"lon": 72.001, "lat": 19.001},
                    {"lon": 72, "lat": 19.001},
                ],
            },
        ],
    })

    assert [building["id"] for building in parsed] == ["way/31"]
