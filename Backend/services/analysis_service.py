"""Application orchestration for area analysis."""
from fastapi import HTTPException
from config import settings
from models.area_models import BoundingBox
from services.geojson_service import analyze_building, buildings_geojson, usable_roof
from services.optimization_service import pack_panels
from services.osm_service import OSMServiceError, fetch_buildings


async def analyze_area(bounds: BoundingBox) -> dict[str, object]:
    """Retrieve buildings and return footprint, rooftop, solar and layout results."""
    try:
        buildings = await fetch_buildings(bounds)
    except OSMServiceError as exc:
        message = str(exc)
        status = 504 if "timed out" in message.lower() else 502
        raise HTTPException(status_code=status, detail=message) from exc
    if not buildings:
        raise HTTPException(status_code=404, detail="No building footprints with usable geometry were found in the selected area.")
    features, optimizations = [], []
    for building in buildings:
        row = analyze_building(building, bounds)
        roof = usable_roof(building["geometry"], bounds)
        row["usable_roof_area_m2"] = round(roof.area, 2)
        row.pop("_projected", None)
        features.append(row)
        if roof.area >= settings.minimum_roof_area_m2:
            optimizations.append({"building_id": building["id"], **pack_panels(roof, bounds)})
    solar_models = [item["solar_model"] for item in optimizations]
    total_panels = sum(item["panel_count"] for item in optimizations)
    return {"area": bounds.model_dump(),
            "buildings": {"count": len(features), "items": features, "geojson": buildings_geojson(buildings, bounds)},
            "solar": {"irradiance_source": "synthetic_demo", "data_class": "synthetic test/demo input; not measured weather data", "annual_irradiance_kwh_m2": settings.synthetic_annual_irradiance_kwh_m2,
                      "location": {"latitude": (bounds.sw_lat + bounds.ne_lat) / 2, "longitude": (bounds.sw_lng + bounds.ne_lng) / 2},
                      "solar_position_method": solar_models[0]["solar_position"]["calculation"] if solar_models else "PVLib when installed"},
            "optimization": {"total_panels": total_panels,
                             "installed_capacity_kw": round(sum(item["installed_capacity_kw"] for item in optimizations), 2),
                             "annual_energy_kwh": round(sum(item["annual_energy_kwh"] for item in optimizations), 2),
                             "buildings": optimizations}}
