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

Install the requirements, then from `Backend/` run `python -m pytest`. Tests mock Overpass for endpoint analysis and do not make live external requests.
