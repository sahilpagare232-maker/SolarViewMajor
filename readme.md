# SunScapeAI (SolarView)

SunScapeAI is a web application for exploring estimated rooftop solar potential in a selected geographic area. A user searches for a place, draws an area on the map, retrieves building footprints from OpenStreetMap, and views estimated rooftop layouts and energy summaries. A separate 3D view lets the user select an individual building and request a panel layout.

This repository contains a React/Vite frontend and a Python/FastAPI backend. The current solar figures are estimates based on a configured synthetic irradiance value; they are not measured weather data, a financial forecast, or a detailed PV system simulation.

## What the application does

1. The user searches for a location and draws a rectangular area on the map.
2. The frontend sends the rectangle's southwest and northeast coordinates to the backend.
3. The backend queries the OpenStreetMap Overpass API for building footprints, processes the returned geometries, and creates GeoJSON.
4. Building footprints are projected into a local metric coordinate system for area and roof-layout calculations.
5. The backend approximates usable roof area by applying a setback to each footprint and packs panels in two grid orientations.
6. It returns building data, panel layouts, installed capacity, and estimated energy. The frontend displays these results on a map, in a table, and in a Cesium 3D view.

## Current capabilities and limitations

- Search a location, draw a rectangular area, and view the analyzed buildings on a Leaflet map.
- Review footprint area, estimated usable roof area, tagged building height (when present), panel count, capacity, and estimated annual energy.
- Request a panel layout for a selected building in the Cesium view.
- Receive building geometry in GeoJSON longitude/latitude coordinate order.
- Panel placement is a deterministic geometric grid heuristic. It compares 0° and 90° layouts, maximizing panel count and using covered area as a tie-breaker; it is not a global optimizer or an AI/RL model.
- Roof area is approximated from the building footprint. Roof pitch, obstructions, shading, structural suitability, and actual roof surfaces are not modeled.
- Missing OSM building heights remain unknown. A display-only placeholder in the 3D viewer does not turn an unknown height into measured data.
- Annual irradiance defaults to a configurable synthetic demo value. PVLib is used for a solar-position calculation when available, not for a detailed weather-driven PV production simulation. Energy output is explicitly an estimate.
- OpenStreetMap and public Overpass availability, coverage, and rate limits affect data retrieval. Keep selected areas small.
- The repository includes synthetic data files, but the live API currently uses its configured synthetic irradiance setting rather than loading those files as live measured weather input.

## Technology

| Area | Technologies |
| --- | --- |
| Frontend | React, JavaScript, Vite, React Router |
| 2D map | Leaflet, React-Leaflet, Leaflet Draw |
| 3D map | Cesium |
| Backend API | Python, FastAPI, Pydantic, Uvicorn |
| Geographic processing | Shapely, pyproj, GeoJSON |
| Solar estimate | NumPy, pandas, PVLib (solar position when installed) |
| Building source | OpenStreetMap via the public Overpass API |

## Repository layout

```text
Backend/
  api/routes/area.py             Area analysis and selected-building API routes
  models/                        Pydantic request/response and panel models
  services/
    analysis_service.py          Orchestrates area analysis
    grid_service.py              Tiles, fetches, and deduplicates OSM buildings
    osm_service.py               Overpass HTTP requests and errors
    geojson_service.py           Geometry projection, measurements, and GeoJSON
    optimization_service.py      Setback-aware panel layout and selected-building optimizer
    pv_service.py                Solar-position and estimated-energy calculations
  tests/                         Backend API and service tests
  config.py                      Environment-backed backend settings
  main.py                        FastAPI app, CORS, health endpoint
  requirements.txt               Python dependencies
Frontend/
  src/pages/                     Home, map, results, and Cesium pages
  src/maps/                      Leaflet map, drawing control, and search UI
  src/services/                  Backend API and location/solar request helpers
  package.json                   Frontend scripts and dependencies
synthetic_solar_dataset/         Synthetic dataset artifacts
Synth_Data/                      Synthetic data generation code
```

## Prerequisites

- Windows PowerShell (commands below use PowerShell syntax).
- Python 3.11, available as `py -3.11`.
- Node.js 22 or newer and npm.
- Internet access for package installation, map/location services, and Overpass building queries.

## Local setup

### Backend

From the repository root:

```powershell
cd D:\SunScapeAI\Backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, either adjust the execution policy for your user according to your organization's guidance, or skip activation and run `.\.venv\Scripts\python.exe -m pip ...` and `.\.venv\Scripts\python.exe -m uvicorn ...` explicitly.

Create `Backend\.env` from `Backend\.env.example` if you need local overrides and do not already have a local `.env`:

```powershell
Copy-Item .env.example .env
```

Keep local environment files and credentials private. Share `.env.example`, not a populated `.env`.

Start the API from `Backend\` with the virtual environment active:

```powershell
python -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Health check: `http://127.0.0.1:8000/health`. Interactive API docs: `http://127.0.0.1:8000/docs`.

### Frontend

In a second PowerShell terminal:

```powershell
cd D:\SunScapeAI\Frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Vite proxies `/api` requests to `http://127.0.0.1:8000`; start the backend as well to use area analysis and building optimization.
The Vite Cesium plugin serves Cesium's workers and static data under `/cesium/`; keep the plugin enabled when changing the Vite config.

Useful frontend commands, run from `Frontend\`:

```powershell
npm run lint
npm run build
npm run preview
```

Useful backend commands, run from `Backend\` with the venv active:

```powershell
python -m pytest tests
```

The endpoint tests mock Overpass and should not make live external requests. `Backend\service_test.py` is a legacy manual Overpass script, not part of the pytest suite.

## API overview

All area bounds use decimal degrees. Southwest values must be less than northeast values; antimeridian-crossing selections are not supported.

### `GET /health`

Returns `{"status":"ok"}` when the API process is running.

### `POST /api/analyze-area`

Analyzes buildings in a bounding box. `/api/area` is a backward-compatible alias.

Request:

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

The response contains:

- `area`: accepted bounding box.
- `buildings.count` and `buildings.items`: building identifiers, available OSM tags, footprint/usable-roof areas, optional height, centroid/orientation information, and geometry.
- `buildings.geojson`: building FeatureCollection for map rendering.
- `solar`: irradiance source and data-class labels, configured annual irradiance, and solar-position method.
- `optimization`: total panel count, estimated installed capacity and annual energy, per-building layouts, and any layout warnings.

### `POST /api/optimize-building`

Optimizes one selected footprint. The request includes a `building_id`, a Polygon or MultiPolygon GeoJSON `geometry`, `coordinates` for the local projection, and optional `height_m` and `panel_config`. The response includes a GeoJSON FeatureCollection in `panel_layout`, panel specifications and counts, capacity/energy estimates, and the assumptions used.

### Common errors

- `422`: invalid bounds, request fields, or building geometry.
- `404`: area query returned no usable building footprints.
- `413`: area/roof exceeds a processing limit.
- `429`: Overpass rate limit.
- `502` / `503` / `504`: upstream Overpass failure or timeout.

Errors use FastAPI's standard JSON `detail` field.

## Configuration

Backend settings are read from environment variables, with optional values in `Backend\.env`. Environment variables take precedence over `.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OVERPASS_URL` | `https://overpass-api.de/api/interpreter` | Overpass endpoint |
| `REQUEST_TIMEOUT` | `60` | Upstream request timeout in seconds |
| `DEFAULT_LATITUDE` / `DEFAULT_LONGITUDE` | `19.0760` / `72.8777` | Default map location |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins, comma-separated |
| `PANEL_WIDTH_M` / `PANEL_LENGTH_M` | `1.1` / `1.8` | Default panel dimensions in metres |
| `PANEL_POWER_W` | `400` | Default panel rating |
| `PANEL_EFFICIENCY` | `0.20` | Default panel efficiency setting |
| `PANEL_SPACING_M` | `0.05` | Gap between panels in metres |
| `ROOF_SETBACK_M` | `0.5` | Roof-edge setback in metres |
| `MINIMUM_ROOF_AREA_M2` | `4` | Minimum usable area considered in area analysis |
| `DEFAULT_TILT` / `DEFAULT_AZIMUTH` | `20` / `180` | Default solar settings |
| `SYNTHETIC_ANNUAL_IRRADIANCE_KWH_M2` | `1700` | Synthetic demo irradiance input; not a measured weather feed |

## Development notes

- Keep frontend API calls in `Frontend/src/services/` and backend route handling in `Backend/api/routes/`; put domain operations in backend services.
- Validate API inputs with the Pydantic models in `Backend/models/`.
- Preserve the GeoJSON coordinate convention `[longitude, latitude]` when working with geographic geometries.
- Geometry areas and panel packing must use a projected metric CRS, not raw latitude/longitude degrees.
- Tests for external data should mock the upstream service. Avoid relying on public Overpass availability in automated tests.
- Clearly label synthetic, estimated, and OSM-derived values. Do not describe synthetic irradiance as measured data or the deterministic grid heuristic as AI/ML optimization.
- Do not commit local virtual environments, generated caches, or credentials.

## Troubleshooting

| Symptom | Checks |
| --- | --- |
| Frontend cannot reach the API | Confirm the backend is running on `127.0.0.1:8000`; check the Vite `/api` proxy and browser console. |
| Backend dependencies are missing | Activate `Backend\.venv` and reinstall with `python -m pip install -r requirements.txt`. |
| No buildings are returned | Try a nearby area with OSM building coverage; verify the selected rectangle and upstream Overpass availability. |
| Overpass request fails or times out | Reduce the selected area and retry later; public Overpass instances enforce resource and rate limits. |
| Browser reports a CORS error | Set `CORS_ORIGINS` to the exact local frontend origin, then restart the backend. |
| Results differ from expected real-world output | The current irradiance input is synthetic and roof surfaces/shading are simplified; treat the result as a demo estimate. |
