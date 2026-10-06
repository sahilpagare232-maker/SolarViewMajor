"""PVLib-backed power estimation with a documented deterministic fallback."""
from datetime import datetime, timezone
from config import settings


def estimate_panel_annual_energy(latitude: float, longitude: float, panel_count: int, panel_power_w: float, irradiance_kwh_m2: float | None = None) -> dict[str, object]:
    """Estimate one system's annual output; fallback input is explicitly synthetic."""
    source = "synthetic_demo"
    irradiation = irradiance_kwh_m2 if irradiance_kwh_m2 is not None else settings.synthetic_annual_irradiance_kwh_m2
    if irradiance_kwh_m2 is not None:
        source = "provided_irradiance"
    try:
        import pandas as pd
        from pvlib.location import Location
        timestamp = pd.DatetimeIndex([datetime(2026, 6, 21, 12, tzinfo=timezone.utc)])
        position = Location(latitude, longitude).get_solarposition(timestamp)
        elevation = float(position["apparent_elevation"].iloc[0])
        azimuth = float(position["azimuth"].iloc[0])
        dc_power_w = max(0.0, panel_count * panel_power_w * 0.86 * min(1.0, max(0.0, elevation / 90)))
        pvlib_used = True
    except (ImportError, ModuleNotFoundError):
        elevation, azimuth = None, None
        dc_power_w = panel_count * panel_power_w * 0.86
        pvlib_used = False
    annual_kwh = round(panel_count * panel_power_w / 1000 * irradiation * 0.80, 2)
    return {"irradiance_source": source, "annual_irradiance_kwh_m2": irradiation,
            "solar_position": {"calculation": "PVLib" if pvlib_used else "unavailable", "sample_utc": "2026-06-21T12:00:00Z", "elevation_deg": elevation, "azimuth_deg": azimuth},
            "dc_power_w_estimate": round(dc_power_w, 2), "ac_power_w_estimate": round(dc_power_w * 0.96, 2),
            "daily_energy_kwh_estimate": round(annual_kwh / 365, 2), "monthly_energy_kwh_estimate": round(annual_kwh / 12, 2), "annual_energy_kwh_estimate": annual_kwh,
            "energy_data_class": "estimated from synthetic/demo irradiance" if source == "synthetic_demo" else "estimated from provided irradiance"}
