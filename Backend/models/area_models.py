"""Request and response schemas for area analysis."""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sw_lat: float = Field(ge=-90, le=90)
    sw_lng: float = Field(ge=-180, le=180)
    ne_lat: float = Field(ge=-90, le=90)
    ne_lng: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def ordered_bounds(self) -> "BoundingBox":
        if self.sw_lat >= self.ne_lat:
            raise ValueError("sw_lat must be less than ne_lat")
        if self.sw_lng >= self.ne_lng:
            raise ValueError("sw_lng must be less than ne_lng; antimeridian-crossing areas are not supported")
        return self


class AreaRequest(BaseModel):
    coordinates: BoundingBox


class AnalysisResponse(BaseModel):
    area: BoundingBox
    buildings: dict[str, Any]
    solar: dict[str, Any]
    optimization: dict[str, Any]
