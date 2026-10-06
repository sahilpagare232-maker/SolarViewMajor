"""Building analysis schema."""
from typing import Any
from pydantic import BaseModel


class BuildingAnalysis(BaseModel):
    building_id: str
    building_type: str | None = None
    height: float | None = None
    area_m2: float
    centroid: dict[str, float]
    orientation_deg: float | None = None
    usable_roof_area_m2: float
    geometry: dict[str, Any]
