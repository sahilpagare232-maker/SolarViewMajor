"""Area analysis endpoints."""
from fastapi import APIRouter, HTTPException
from models.area_models import AnalysisResponse, AreaRequest
from models.building_models import BuildingOptimizationRequest
from services.analysis_service import analyze_area
from services.optimization_service import optimize_building_with_agent

router = APIRouter(prefix="/api", tags=["area"])


@router.post("/analyze-area", response_model=AnalysisResponse)
async def analyze_area_endpoint(request: AreaRequest) -> dict[str, object]:
    """Analyze OSM footprints, optionally skipping calculations for a fast 3D load."""
    return await analyze_area(request.coordinates, include_optimization=request.include_optimization)


@router.post("/area")
async def legacy_area_endpoint(request: AreaRequest) -> dict[str, object]:
    """Backward-compatible alias used by the current React area selector."""
    return await analyze_area(request.coordinates)


@router.post("/optimize-building")
async def optimize_building_endpoint(request: BuildingOptimizationRequest) -> dict[str, object]:
    """Return a panel layout for the building the user selected in Cesium."""
    try:
        return await optimize_building_with_agent(
            building_id=request.building_id,
            geometry_geojson=request.geometry,
            bounds=request.coordinates,
            panel=request.panel_config,
            height_m=request.height_m,
        )
    except ValueError as exc:
        status_code = 413 if "too many panel candidates" in str(exc).lower() else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
