# Solar Potential backend

FastAPI backend for the React, Leaflet, and Cesium application. Run commands from `Backend/`.

## Setup and run

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

The API listens on `http://127.0.0.1:8000`; interactive docs are at `/docs`.

## Main workflow

`POST /api/analyze-area` fetches OpenStreetMap building footprints in the submitted `coordinates` bounds. The default request also estimates roof areas and creates a basic panel layout for map analysis. The Cesium view sends `include_optimization: false`, which returns lightweight footprint geometry and skips roof projection, panel packing, and solar calculations so the 3D viewer opens faster.

`POST /api/optimize-building` runs for the building the user selects in Cesium. It repairs eligible polygon geometry, projects it to local UTM metres, applies a roof-edge setback, checks two grid orientations against panel dimensions and spacing, and returns panel polygons as a GeoJSON `FeatureCollection`. The geometric placement step is deterministic and fast; it maximizes feasible panel count between those two orientations, not a global roof-layout optimum. OSM footprints are treated as flat roofs; pitch, roof obstacles, and shade are unavailable.

The selected-building endpoint is orchestrated as a **Solar placement agent**: inspect the footprint, find feasible panel coordinates, estimate output, and validate the returned polygons. Its engineering constraints and geometric packer decide panel locations. A small supervised ML regressor estimates DC power for those placements. This is a hybrid ML-assisted workflow, not reinforcement learning or an LLM agent.

## Solar and ML data

For selected-building estimates, the backend requests a typical meteorological year from the [PVGIS API](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/api-non-interactive-service_en), applies PVLib solar position, plane-of-array irradiance and cell-temperature calculations, then uses the trained regressor for DC power. It applies configured system and inverter losses. PVGIS data represents a historical typical year, not a live forecast or site measurement. If the provider is unavailable or times out, the endpoint returns a clearly labeled PVLib clear-sky fallback, which does not model clouds. Weather is cached by rounded location.

The model is trained on generated PVLib simulations, not measured plant data. The synthetic dataset varies location, weather, shading factor, temperature, wind, panel rating, tilt, and azimuth. Its held-out metrics measure agreement with the PVLib simulation labels only; they do not demonstrate real-world forecast accuracy. To regenerate the CSV and fit the model, from `Backend/` run:

```powershell
..\.venv\Scripts\python.exe ..\Synth_Data\generate_synData.py
python -m ml.train_model
```

Training outputs `Backend/ml/solar_power_model.json`; generated examples are written to `synthetic_solar_data.csv` at the project root. `PVGIS_API_URL` and `PVGIS_TIMEOUT_SECONDS` configure the weather provider. Area-wide preview estimates use the cached local PVLib clear-sky model to avoid making a remote weather call for each building.

## Other details

- Footprints and optional height tags come from OpenStreetMap; absent heights remain unknown. Cesium uses a display-only extrusion for untagged heights.
- Coordinates in GeoJSON use `[longitude, latitude]` order. Areas use a local metric projection for roof measurements.
- Keep Overpass requests small; the public service can rate-limit or time out. No fake building data is substituted on errors.
- `GET /health` returns `{"status":"ok"}`. The legacy `POST /api/area` alias remains available.

## Tests

From `Backend/`, run `python -m pytest tests`. Tests mock Overpass and PVGIS and do not require live external requests.
