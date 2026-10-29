"""Building analysis schema."""
from typing import Any
from pydantic import BaseModel, Field

from models.area_models import BoundingBox
from models.solar_models import PanelConfig


class BuildingAnalysis(BaseModel):
    building_id: str
    building_type: str | None = None
    height: float | None = None
    area_m2: float
    centroid: dict[str, float]
    orientation_deg: float | None = None
    usable_roof_area_m2: float
    geometry: dict[str, Any]


class BuildingOptimizationRequest(BaseModel):
    """Selected building footprint and optional panel settings for one-roof placement."""

    building_id: str = Field(min_length=1, max_length=160)
    geometry: dict[str, Any]
    coordinates: BoundingBox
    height_m: float | None = Field(default=None, gt=0, le=1000)
    panel_config: PanelConfig | None = None
