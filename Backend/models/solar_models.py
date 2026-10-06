"""Solar and photovoltaic input schemas."""
from pydantic import BaseModel, Field


class PanelConfig(BaseModel):
    width_m: float = Field(default=1.1, gt=0)
    length_m: float = Field(default=1.8, gt=0)
    rated_power_w: float = Field(default=400, gt=0)
    efficiency: float = Field(default=0.20, gt=0, le=1)
    spacing_m: float = Field(default=0.05, ge=0)
    setback_m: float = Field(default=0.5, ge=0)
