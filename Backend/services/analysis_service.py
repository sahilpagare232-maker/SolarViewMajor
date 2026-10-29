"""Application orchestration for area analysis."""
from fastapi import HTTPException
from config import settings
from models.area_models import BoundingBox
from services.geojson_service import analyze_building, buildings_geojson, usable_roof
from services.optimization_service import pack_panels
from services.osm_service import OSMServiceError
from services.grid_service import fetch_grid_buildings


async def analyze_area(bounds: BoundingBox, *, include_optimization: bool = True) -> dict[str, object]:
    """Retrieve buildings and return footprint, rooftop, solar and layout results."""
    try:
        buildings = await fetch_grid_buildings(bounds)
    except OSMServiceError as exc:
        message = str(exc)
        status = (
            exc.status_code
            if exc.status_code in {413, 429, 502, 503, 504}
            else 504 if "timed out" in message.lower() else 502
        )
        raise HTTPException(status_code=status, detail=message) from exc
    if not buildings:
        raise HTTPException(status_code=404, detail="No building footprints with usable geometry were found in the selected area.")
    if not include_optimization:
        return {
            "area": bounds.model_dump(),
            "buildings": {
                "count": len(buildings),
                "items": [],
                "geojson": buildings_geojson(buildings, bounds, detailed=False),
            },
            "solar": {
                "irradiance_source": "not_requested",
                "data_class": "Solar analysis skipped; this request fetched footprints for the 3D viewer only.",
            },
            "optimization": {
                "total_panels": 0,
                "installed_capacity_kw": 0,
                "annual_energy_kwh": 0,
                "warnings": [],
                "buildings": [],
            },
        }
    features, optimizations, optimization_warnings = [], [], []
    for building in buildings:
        row = analyze_building(building, bounds)
        roof = usable_roof(building["geometry"], bounds)
        row["usable_roof_area_m2"] = round(roof.area, 2)
        row.pop("_projected", None)
        features.append(row)
        if roof.area >= settings.minimum_roof_area_m2:
            try:
                optimizations.append({
                    "building_id": building["id"],
                    **pack_panels(
                        roof,
                        bounds,
                        height_m=row["height"],
                        setback_already_applied=True,
                    ),
                })
            except ValueError as exc:
                optimization_warnings.append({"building_id": building["id"], "detail": str(exc)})
    solar_models = [item["solar_model"] for item in optimizations]
    representative_solar = solar_models[0] if solar_models else {}
    total_panels = sum(item["panel_count"] for item in optimizations)
    return {"area": bounds.model_dump(),
            "buildings": {"count": len(features), "items": features, "geojson": buildings_geojson(buildings, bounds)},
            "solar": {"irradiance_source": representative_solar.get("irradiance_source", "not_calculated"),
                      "data_class": representative_solar.get("energy_data_class", "Solar output was not calculated for this area."),
                      "annual_irradiance_kwh_m2": representative_solar.get("annual_irradiance_kwh_m2"),
                      "location": {"latitude": (bounds.sw_lat + bounds.ne_lat) / 2, "longitude": (bounds.sw_lng + bounds.ne_lng) / 2},
                      "solar_position_method": solar_models[0]["solar_position"]["calculation"] if solar_models else "PVLib"},
            "optimization": {"total_panels": total_panels,
                             "installed_capacity_kw": round(sum(item["installed_capacity_kw"] for item in optimizations), 2),
                             "annual_energy_kwh": round(sum(item["annual_energy_kwh"] for item in optimizations), 2),
                             "warnings": optimization_warnings,
                             "buildings": optimizations}}
