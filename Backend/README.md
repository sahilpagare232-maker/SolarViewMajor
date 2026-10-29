# Solar Potential backend

FastAPI backend for the existing React and Leaflet application. Run commands from this directory.

## Setup and run

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

The API listens on `http://127.0.0.1:8000`. Interactive OpenAPI documentation is at `/docs`; JSON schema is at `/openapi.json`. Copy `.env.example` to `.env` to configure local settings; environment variables override values from that file.

## Endpoints

`GET /health` returns `{"status":"ok"}`.

`POST /api/analyze-area` accepts the current frontend bounding-box shape. `/api/area` is retained as an alias for the current frontend call.

```json
{
  "coordinates": {
    "sw_lat": 19.07545,
    "sw_lng": 72.87908,
    "ne_lat": 19.07715,
    "ne_lng": 72.88333
  }
}
```

`POST /api/optimize-building` accepts the selected building footprint from the Cesium view and returns its panel polygons as a GeoJSON `FeatureCollection`. The request uses the same `coordinates` bounds returned by area analysis:

```json
{
  "building_id": "way/12345",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[72.0, 19.0], [72.0001, 19.0], [72.0001, 19.0001], [72.0, 19.0001], [72.0, 19.0]]]
  },
  "coordinates": {
    "sw_lat": 18.99,
    "sw_lng": 71.99,
    "ne_lat": 19.02,
    "ne_lng": 72.02
  },
  "height_m": 12
}
```

The endpoint repairs simple invalid polygon rings when possible, projects geometry to local UTM metres, applies the configured edge setback, and evaluates deterministic grid layouts at 0° and 90°. It maximizes feasible panel count, then uses covered area as a tie-breaker. The result includes panel dimensions, spacing, orientation, elevation when tagged, capacity, approximate coverage, energy estimate, and explicit flat-roof assumptions. Invalid geometry returns `422`; roofs exceeding the candidate-work limit return `413`.

Cesium's building click handler sends only the selected feature to this endpoint. It renders returned panel polygons as a separate data source. Untagged heights stay `null` in the API; the viewer uses the existing 10 m placeholder only to display panels on an extrusion.

The optimizer is a deterministic geometric heuristic, not reinforcement learning and not a proven global optimum. An RL policy could later be added behind the optimizer service interface, with this geometry-validating grid method retained as its fallback. No suitable roof-layout training set currently exists, so this project does not train or claim an RL model.

Successful responses contain `area`, `buildings.count`, `buildings.items`, renderable `buildings.geojson`, solar metadata, and per-building panel layouts under `optimization.buildings`. Panel polygons and OSM footprints are GeoJSON in `[longitude, latitude]` order. For example, a synthetic/mock-backed response has this shape:

```json
{
  "area": {"sw_lat": 19.075, "sw_lng": 72.879, "ne_lat": 19.077, "ne_lng": 72.883},
  "buildings": {"count": 1, "items": [], "geojson": {"type": "FeatureCollection", "features": []}},
  "solar": {"irradiance_source": "synthetic_demo", "data_class": "synthetic test/demo input; not measured weather data", "annual_irradiance_kwh_m2": 1700},
  "optimization": {"total_panels": 0, "installed_capacity_kw": 0, "annual_energy_kwh": 0, "buildings": []}
}
```

Errors use FastAPI's standard `{"detail":"..."}` format: `422` for invalid coordinates, `404` when no usable building geometry is found, `504` for Overpass timeouts, and `502` for other Overpass failures. No offline fallback fabricates building data.

## Data and modeling limits

- Building footprints and tagged heights come from OpenStreetMap. Missing or unparseable heights are `null`.
- Areas use a local UTM projection selected for the selected bounds, not degree-space calculations. Rooftops are approximated by inward-buffered building footprints; this does not model roof pitch, obstacles, shading, or actual roof surfaces.
- No live weather or irradiance provider is configured. `SYNTHETIC_ANNUAL_IRRADIANCE_KWH_M2` is explicitly synthetic demo input, and resulting energy is an estimate, never a measured forecast.
- PVLib is used for solar position when installed. DC/AC and annual energy are transparent engineering estimates with simple loss factors; a validated PV module and inverter model plus measured weather data are required for a physically detailed PVLib production simulation.
- Panel placement uses deterministic axis-aligned grid packing inside the estimated usable roof area. It does not optimize roof orientation or shading.
- Antimeridian-crossing bounds are rejected. Keep selected areas small to avoid public Overpass rate/timeout limits.

## Tests

Install the requirements, then from `Backend/` run `python -m pytest tests`. Tests mock Overpass for endpoint analysis and do not make live external requests. (`service_test.py` is a legacy manual Overpass script, not part of the pytest suite.)
