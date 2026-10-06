"""Area analysis endpoints."""
from fastapi import APIRouter
from models.area_models import AnalysisResponse, AreaRequest
from services.analysis_service import analyze_area

router = APIRouter(prefix="/api", tags=["area"])


@router.post("/analyze-area", response_model=AnalysisResponse)
async def analyze_area_endpoint(request: AreaRequest) -> dict[str, object]:
    """Analyze real OSM footprints for the submitted geographic bounding box."""
    return await analyze_area(request.coordinates)


@router.post("/area")
async def legacy_area_endpoint(request: AreaRequest) -> dict[str, object]:
    """Backward-compatible alias used by the current React area selector."""
    return await analyze_area(request.coordinates)
