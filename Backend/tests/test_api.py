from fastapi.testclient import TestClient
from main import app
from services.analysis_service import analyze_area

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_invalid_bounds_rejected():
    response = client.post("/api/analyze-area", json={"coordinates": {"sw_lat": 20, "sw_lng": 72, "ne_lat": 19, "ne_lng": 73}})
    assert response.status_code == 422


def test_analysis_with_mocked_osm(monkeypatch):
    from shapely.geometry import Polygon
    async def mocked_fetch(_bounds):
        return [{"id": "way/12", "tags": {"building": "yes"}, "geometry": Polygon([(72, 19), (72.001, 19), (72.001, 19.001), (72, 19.001)])}]
    monkeypatch.setattr("services.analysis_service.fetch_buildings", mocked_fetch)
    response = client.post("/api/analyze-area", json={"coordinates": {"sw_lat": 19, "sw_lng": 72, "ne_lat": 19.01, "ne_lng": 72.01}})
    assert response.status_code == 200
    assert response.json()["buildings"]["count"] == 1
