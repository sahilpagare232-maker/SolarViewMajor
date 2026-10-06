# Solar Potential & Panel Optimization System

An intelligent web-based system for estimating the solar energy potential of buildings and optimizing solar panel placement using geographic data, building geometry, solar irradiance, and photovoltaic models.

The system allows a user to search for a location, select an area on an interactive map, retrieve building information, analyze available rooftop surfaces, estimate solar energy generation, and determine suitable solar panel placements.

---

## 1. Project Objective

The main objective of this project is to develop a system that can:

- Allow users to search for a location.
- Display the selected location on an interactive map.
- Allow users to select an area for analysis.
- Retrieve building footprints within the selected area.
- Convert building data into GeoJSON.
- Analyze rooftop/building geometry.
- Estimate solar irradiance and sunlight availability.
- Determine suitable areas for solar panel installation.
- Calculate estimated solar energy generation.
- Estimate system capacity and potential electricity generation.
- Optimize panel placement based on available rooftop area and solar conditions.
- Provide the results through a simple web interface.

The project combines **GIS, solar-energy modeling, optimization, and AI-assisted analysis**.

---

# 2. System Architecture

```text
                         ┌──────────────────────┐
                         │        USER          │
                         │ Search / Select Area │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │         FRONTEND           │
                    │      React + Leaflet       │
                    │                            │
                    │ • Search Location          │
                    │ • Interactive Map           │
                    │ • Area Selection            │
                    │ • Display Results            │
                    └─────────────┬──────────────┘
                                  │
                              HTTP / JSON
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │          BACKEND            │
                    │          FastAPI            │
                    │                            │
                    │ • Area Processing            │
                    │ • Building Data             │
                    │ • GeoJSON Processing        │
                    │ • Solar Calculations        │
                    │ • Panel Optimization        │
                    └─────────────┬──────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
        ┌───────────┐       ┌───────────┐       ┌───────────┐
        │   OSM /   │       │  Solar /  │       │  PVLib    │
        │ Overpass  │       │ Weather   │       │           │
        │           │       │   Data    │       │ PV Model  │
        └───────────┘       └───────────┘       └───────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │ Optimization / AI   │
                       │                     │
                       │ Panel Placement     │
                       │ Energy Estimation   │
                       │ Cost Analysis       │
                       └─────────────────────┘
```

---

# 3. Technology Stack

## Frontend

- React
- JavaScript
- Leaflet
- React-Leaflet
- HTML/CSS

The frontend is responsible for map interaction, location search, area selection, and displaying analysis results.

---

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- GeoPandas
- Shapely
- NumPy
- Pandas

The backend handles geographic processing, building data retrieval, solar calculations, and optimization.

---

## Geographic Data

### OpenStreetMap

OpenStreetMap is used as the primary source for building and geographic information.

Building data can be retrieved through:

- Overpass API
- OSM data
- GeoJSON conversion

The system should preserve accurate building geometries whenever possible.

---

## Solar Modeling

### PVLib

PVLib is used for photovoltaic and solar-energy calculations.

PVLib can be used for:

- Solar position
- Irradiance calculations
- Plane-of-array irradiance
- PV system modeling
- Energy estimation
- Temperature effects
- DC/AC power estimation

---

## 4. Core Workflow

```text
User searches location
        ↓
Location displayed on map
        ↓
User selects area
        ↓
Frontend sends selected coordinates
        ↓
FastAPI receives area
        ↓
Building data retrieved
        ↓
Building geometry converted to GeoJSON
        ↓
Building rooftops analyzed
        ↓
Solar/irradiance data obtained
        ↓
Solar potential calculated
        ↓
Suitable rooftop areas identified
        ↓
Solar panels positioned
        ↓
PV energy generation estimated
        ↓
Optimization performed
        ↓
Results returned to frontend
        ↓
User views solar potential
```

---

# 5. Frontend

The frontend provides an interactive map-based interface.

### Main features

### Location Search

Users can search for an address or location.

The map moves to the selected location.

### Area Selection

The user can draw/select an area on the map.

The selected area is converted into geographic coordinates.

Example:

```json
{
  "coordinates": {
    "sw_lat": 19.123,
    "sw_lng": 73.123,
    "ne_lat": 19.130,
    "ne_lng": 73.135
  }
}
```

The coordinates are sent to the backend.

### Map

Leaflet is used to display:

- OpenStreetMap tiles
- Search results
- Building footprints
- GeoJSON
- Solar analysis results
- Panel placement

---

# 6. Backend

The backend is implemented using FastAPI.

Example structure:

```text
backend/
│
├── main.py
│
├── api/
│   ├── routes/
│   │   ├── area.py
│   │   ├── buildings.py
│   │   ├── solar.py
│   │   └── optimization.py
│
├── services/
│   ├── osm_service.py
│   ├── geojson_service.py
│   ├── solar_service.py
│   ├── pv_service.py
│   └── optimization_service.py
│
├── models/
│   ├── area_models.py
│   ├── building_models.py
│   └── solar_models.py
│
├── utils/
│   ├── geometry.py
│   └── coordinates.py
│
└── requirements.txt
```

The exact structure can be simplified during the initial implementation.

---

# 7. Building Data

Building footprints are obtained from OpenStreetMap.

The backend sends a query to Overpass using the selected geographic area.

Conceptually:

```text
Selected Area
      ↓
Overpass API
      ↓
OSM Building Data
      ↓
Building IDs / Geometry
      ↓
GeoJSON
```

The system should retrieve building geometry rather than only building IDs.

---

# 8. GeoJSON

GeoJSON is used as the primary format for transferring geographic geometry between the backend and frontend.

Example:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "building_id": "12345"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": []
      }
    }
  ]
}
```

GeoJSON allows the frontend to directly display building geometries using Leaflet.

---

# 9. Building/Rooftop Analysis

For every building, the system should analyze:

- Building footprint
- Building area
- Polygon geometry
- Orientation
- Possible rooftop area
- Building height when available
- Roof suitability
- Potential panel area

Not every building footprint is automatically suitable for solar panels.

The system should consider constraints such as:

- Minimum usable area
- Panel dimensions
- Panel spacing
- Roof orientation
- Roof inclination when available
- Shading
- Building boundaries
- Safety margins

---

# 10. Solar Irradiance

Solar irradiance represents the amount of solar radiation received by a surface.

Important quantities include:

### GHI

Global Horizontal Irradiance.

Solar radiation received by a horizontal surface.

### DNI

Direct Normal Irradiance.

Direct solar radiation received perpendicular to the Sun's rays.

### DHI

Diffuse Horizontal Irradiance.

Solar radiation scattered by the atmosphere.

These values can be used together to calculate irradiance on the plane of the solar panel.

---

# 11. Solar Position

The position of the Sun changes throughout the day and year.

Important parameters include:

- Solar azimuth
- Solar elevation
- Zenith angle

PVLib can calculate solar position using:

```text
Latitude
Longitude
Date
Time
Timezone
```

This allows the system to determine the Sun's position for solar-energy calculations.

---

# 12. PVLib

PVLib is the primary photovoltaic modeling library.

The system can use PVLib for:

```text
Location
   ↓
Solar Position
   ↓
Irradiance
   ↓
Plane-of-Array Irradiance
   ↓
PV Module Model
   ↓
DC Power
   ↓
Inverter
   ↓
AC Power
   ↓
Energy
```

---

# 13. Solar Energy Estimation

A simplified energy calculation is:

```text
Energy = Irradiance × Panel Area × Panel Efficiency × System Efficiency
```

For more accurate modeling, PVLib should be used instead of relying only on this simplified formula.

The final system can estimate:

- Daily energy
- Monthly energy
- Annual energy
- Installed capacity
- Peak power
- Estimated AC output

---

# 14. Panel Placement

Panel placement is one of the main optimization tasks.

The system should determine how many panels can fit on a suitable rooftop area.

Inputs include:

```text
Roof Geometry
Panel Width
Panel Length
Panel Efficiency
Panel Power
Panel Orientation
Panel Tilt
Required Spacing
```

The optimization process attempts to maximize:

```text
Solar Energy Generation
```

while satisfying:

```text
Available Roof Area
Panel Dimensions
Spacing
Roof Boundaries
Orientation
Shading
```

---

# 15. Optimization

The optimization layer can determine:

- Number of panels
- Panel locations
- Panel orientation
- Panel tilt
- Expected energy generation
- Suitable rooftop regions

A future optimization model can use:

```text
Objective:
Maximize annual solar energy

Subject to:
Panel must remain inside roof
Panel spacing constraints
Available area constraints
Orientation constraints
Shading constraints
```

---

# 16. AI / Agent Layer

The project can optionally use an AI agent architecture.

Possible agents include:

```text
                 ┌─────────────────────┐
                 │    Main AI Agent    │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
    ┌───────────┐     ┌────────────┐    ┌─────────────┐
    │ Solar     │     │ Panel      │    │ Cost / ROI  │
    │ Agent     │     │ Agent      │    │ Agent       │
    └───────────┘     └────────────┘    └─────────────┘
```

### Solar Agent

Responsible for:

- Solar irradiance
- Solar position
- Energy estimation

### Panel Agent

Responsible for:

- Panel placement
- Number of panels
- Roof utilization

### Cost Agent

Responsible for:

- Installation cost
- Estimated electricity generation
- Savings
- ROI
- Payback period

LangChain can be introduced later if the AI-agent layer becomes necessary.

The core scientific calculations should remain deterministic and should not depend on an LLM.

---

# 17. API Design

Example API endpoints:

### Health Check

```http
GET /health
```

### Analyze Area

```http
POST /api/analyze-area
```

Request:

```json
{
  "coordinates": {
    "sw_lat": 19.123,
    "sw_lng": 73.123,
    "ne_lat": 19.130,
    "ne_lng": 73.135
  }
}
```

Response:

```json
{
  "buildings": [],
  "geojson": {},
  "solar": {},
  "optimization": {}
}
```

---

# 18. Error Handling

The system should gracefully handle:

- Invalid coordinates
- Empty areas
- No buildings found
- Overpass timeout
- API errors
- Invalid GeoJSON
- Missing building attributes
- Missing solar data
- Large selected areas

Overpass requests should use reasonable query sizes and timeout handling.

---

# 19. Performance Considerations

The system should avoid unnecessarily large Overpass requests.

Recommended approach:

```text
Small area
   ↓
Overpass query
   ↓
Process buildings
   ↓
Cache results
   ↓
Solar analysis
```

For larger areas, the system should:

- Limit query size
- Split requests if necessary
- Cache building data
- Avoid repeated API calls
- Process buildings independently

---

# 20. Accuracy Considerations

OpenStreetMap provides useful building footprints but does not guarantee accurate:

- Building height
- Roof height
- Roof type
- Roof inclination
- Roof orientation

For improved accuracy, the project can later integrate additional sources such as:

- LiDAR
- Digital Surface Models
- Digital Elevation Models
- Satellite imagery
- Building height datasets

The system should distinguish between **measured/observed values** and **estimated values**.

---

# 21. Future Improvements

Potential future features include:

- LiDAR-based building height
- 3D building reconstruction
- Roof slope detection
- Shadow simulation
- Satellite imagery
- Better weather datasets
- Machine-learning based solar prediction
- Advanced panel optimization
- Electricity tariff integration
- Cost estimation
- ROI calculation
- Battery-storage optimization
- Multiple panel types
- User accounts
- Historical solar analysis
- Detailed PDF reports

---

# 22. Project Goal

The final system should provide a simple workflow:

```text
Search Location
      ↓
Select Area
      ↓
Get Buildings
      ↓
Analyze Rooftops
      ↓
Calculate Solar Potential
      ↓
Optimize Panel Placement
      ↓
Estimate Energy Generation
      ↓
Display Results
```

The system is intended to demonstrate how **GIS + OpenStreetMap + solar modeling + photovoltaic simulation + optimization + AI** can be combined into a practical solar-energy planning platform.