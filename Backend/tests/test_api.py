from fastapi.testclient import TestClient
from main import app
from services.analysis_service import analyze_area
from services.osm_service import OSMServiceError

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_invalid_bounds_rejected():
    response = client.post("/api/analyze-area", json={"coordinates": {"sw_lat": 20, "sw_lng": 72, "ne_lat": 19, "ne_lng": 73}})
    assert response.status_code == 422


def test_analysis_with_mocked_osm(monkeypatch):
    from shapely.geometry import Polygon
    async def mocked_fetch(_bounds):
        return [{"id": "way/12", "tags": {"building": "yes"}, "geometry": Polygon([(72, 19), (72.0001, 19), (72.0001, 19.0001), (72, 19.0001)])}]
    monkeypatch.setattr("services.analysis_service.fetch_grid_buildings", mocked_fetch)
    response = client.post("/api/analyze-area", json={"coordinates": {"sw_lat": 19, "sw_lng": 72, "ne_lat": 19.01, "ne_lng": 72.01}})
    assert response.status_code == 200
    assert response.json()["buildings"]["count"] == 1


def test_footprint_only_analysis_skips_solar_and_panel_work(monkeypatch):
    from shapely.geometry import Polygon

    async def mocked_fetch(_bounds):
        return [{"id": "way/fast", "tags": {"building": "yes"}, "geometry": Polygon([
            (72, 19), (72.0001, 19), (72.0001, 19.0001), (72, 19.0001),
        ])}]

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("full solar analysis should be skipped")

    monkeypatch.setattr("services.analysis_service.fetch_grid_buildings", mocked_fetch)
    monkeypatch.setattr("services.analysis_service.analyze_building", fail_if_called)
    monkeypatch.setattr("services.analysis_service.pack_panels", fail_if_called)
    response = client.post("/api/analyze-area", json={
        "coordinates": {"sw_lat": 19, "sw_lng": 72, "ne_lat": 19.01, "ne_lng": 72.01},
        "include_optimization": False,
    })

    assert response.status_code == 200
    result = response.json()
    assert result["buildings"]["count"] == 1
    assert result["buildings"]["items"] == []
    assert result["buildings"]["geojson"]["features"][0]["properties"]["height"] is None
    assert result["solar"]["irradiance_source"] == "not_requested"
    assert result["optimization"]["buildings"] == []


def test_analysis_reports_no_buildings(monkeypatch):
    async def mocked_fetch(_bounds):
        return []

    monkeypatch.setattr("services.analysis_service.fetch_grid_buildings", mocked_fetch)
    response = client.post("/api/analyze-area", json={"coordinates": {"sw_lat": 19, "sw_lng": 72, "ne_lat": 19.01, "ne_lng": 72.01}})

    assert response.status_code == 404
    assert "No building footprints" in response.json()["detail"]


def test_analysis_preserves_overpass_rate_limit(monkeypatch):
    async def rate_limited(_bounds):
        raise OSMServiceError("Overpass rate-limited the request.", status_code=429)

    monkeypatch.setattr("services.analysis_service.fetch_grid_buildings", rate_limited)
    response = client.post("/api/analyze-area", json={"coordinates": {"sw_lat": 19, "sw_lng": 72, "ne_lat": 19.01, "ne_lng": 72.01}})

    assert response.status_code == 429
    assert "rate-limited" in response.json()["detail"]


def test_optimize_selected_building_returns_cesium_panel_layout(monkeypatch):
    async def mocked_energy(*_args):
        return {
            "irradiance_source": "pvgis_tmy",
            "annual_energy_kwh_estimate": 1200,
            "energy_data_class": "PVGIS typical meteorological year; model estimate.",
            "panel_model": {},
        }

    monkeypatch.setattr("services.optimization_service.estimate_panel_annual_energy_from_tmy", mocked_energy)
    response = client.post("/api/optimize-building", json={
        "building_id": "way/12",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[72.0, 19.0], [72.0001, 19.0], [72.0001, 19.0001], [72.0, 19.0001], [72.0, 19.0]]],
        },
        "coordinates": {"sw_lat": 18.99, "sw_lng": 71.99, "ne_lat": 19.02, "ne_lng": 72.02},
        "height_m": 12,
    })

    assert response.status_code == 200
    result = response.json()
    assert result["building_id"] == "way/12"
    assert result["panel_count"] == len(result["panel_layout"]["features"])
    assert result["installed_capacity_kw"] == round(result["panel_count"] * 0.4, 2)
    assert result["panel_layout"]["type"] == "FeatureCollection"
    assert result["panel_layout"]["features"][0]["properties"]["elevation_m"] == 12
    assert "flat roof" in result["roof_assumption"]
    assert result["annual_energy_data_class"].startswith("PVGIS typical")
    assert result["agent"]["status"] == "complete"
    assert len(result["agent"]["steps"]) == 4


def test_optimize_selected_building_rejects_invalid_geometry():
    response = client.post("/api/optimize-building", json={
        "building_id": "node/12",
        "geometry": {"type": "Point", "coordinates": [72, 19]},
        "coordinates": {"sw_lat": 18.99, "sw_lng": 71.99, "ne_lat": 19.02, "ne_lng": 72.02},
    })

    assert response.status_code == 422
    assert "Polygon or MultiPolygon" in response.json()["detail"]
