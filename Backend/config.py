"""Environment-backed application settings with dependency-free defaults."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    overpass_url: str = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    request_timeout: float = _float_env("REQUEST_TIMEOUT", 60.0)
    default_latitude: float = _float_env("DEFAULT_LATITUDE", 19.0760)
    default_longitude: float = _float_env("DEFAULT_LONGITUDE", 72.8777)
    cors_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")))
    panel_width_m: float = _float_env("PANEL_WIDTH_M", 1.1)
    panel_length_m: float = _float_env("PANEL_LENGTH_M", 1.8)
    panel_power_w: float = _float_env("PANEL_POWER_W", 400.0)
    panel_efficiency: float = _float_env("PANEL_EFFICIENCY", 0.20)
    panel_spacing_m: float = _float_env("PANEL_SPACING_M", 0.05)
    roof_setback_m: float = _float_env("ROOF_SETBACK_M", 0.5)
    minimum_roof_area_m2: float = _float_env("MINIMUM_ROOF_AREA_M2", 4.0)
    default_tilt: float = _float_env("DEFAULT_TILT", 20.0)
    default_azimuth: float = _float_env("DEFAULT_AZIMUTH", 180.0)
    pvgis_api_url: str = os.getenv("PVGIS_API_URL", "https://re.jrc.ec.europa.eu/api/v5_3/")
    pvgis_timeout_seconds: float = _float_env("PVGIS_TIMEOUT_SECONDS", 8.0)
    system_losses_fraction: float = _float_env("SYSTEM_LOSSES_FRACTION", 0.14)
    inverter_efficiency: float = _float_env("INVERTER_EFFICIENCY", 0.96)
    panel_temperature_coefficient: float = _float_env("PANEL_TEMPERATURE_COEFFICIENT", -0.0035)


settings = Settings()
