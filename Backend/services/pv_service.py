"""Weather-based PV estimates using PVGIS TMY or a fast local PVLib clear-sky fallback."""
from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from pvlib import irradiance, temperature
from pvlib.iotools import get_pvgis_tmy
from pvlib.location import Location

from config import settings
from services.ml_solar_service import model_metadata, predict_dc_power_w


def _weather_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize PVGIS names and require the weather fields used for POA and temperature."""
    aliases = {
        "ghi": ("ghi", "G(h)"),
        "dni": ("dni", "Gb(n)"),
        "dhi": ("dhi", "Gd(h)"),
        "temp_air": ("temp_air", "T2m"),
        "wind_speed": ("wind_speed", "WS10m"),
    }
    columns = {}
    for normalized, alternatives in aliases.items():
        match = next((candidate for candidate in alternatives if candidate in data.columns), None)
        if match is None:
            raise ValueError(f"Weather data is missing the {normalized} field.")
        columns[normalized] = data[match].astype(float)
    return pd.DataFrame(columns, index=data.index).replace([np.inf, -np.inf], np.nan).fillna(0)


def _estimate_from_weather(
    weather_data: pd.DataFrame,
    latitude: float,
    longitude: float,
    panel_count: int,
    panel_power_w: float,
    source: str,
    weather_note: str,
) -> dict[str, Any]:
    if panel_count <= 0 or panel_power_w <= 0 or weather_data.empty:
        return _empty_estimate(source, weather_note)

    weather = _weather_columns(weather_data)
    location = Location(latitude, longitude, tz=str(weather.index.tz or "UTC"))
    solar = location.get_solarposition(weather.index)
    plane = irradiance.get_total_irradiance(
        surface_tilt=settings.default_tilt,
        surface_azimuth=settings.default_azimuth,
        solar_zenith=solar["apparent_zenith"],
        solar_azimuth=solar["azimuth"],
        dni=weather["dni"],
        ghi=weather["ghi"],
        dhi=weather["dhi"],
        albedo=0.2,
    )
    poa = plane["poa_global"].fillna(0).clip(lower=0)
    cell_temperature = temperature.faiman(
        poa,
        temp_air=weather["temp_air"],
        wind_speed=weather["wind_speed"].clip(lower=0),
    )
    system_dc_rating_w = panel_count * panel_power_w
    dc_power = predict_dc_power_w(poa.to_numpy(), cell_temperature.to_numpy(), system_dc_rating_w)
    losses = min(max(settings.system_losses_fraction, 0.0), 0.5)
    ac_power = dc_power * (1 - losses) * min(max(settings.inverter_efficiency, 0.0), 1.0)

    intervals = weather.index.to_series().diff().dt.total_seconds().to_numpy() / 3600
    valid_intervals = intervals[np.isfinite(intervals) & (intervals > 0)]
    default_interval = float(np.median(valid_intervals)) if len(valid_intervals) else 1.0
    intervals[0] = default_interval
    intervals = np.where(np.isfinite(intervals) & (intervals > 0), intervals, default_interval)
    annual_energy = float(np.nansum(ac_power * intervals) / 1000)
    capacity_kw = system_dc_rating_w / 1000
    best_index = int(np.argmax(dc_power)) if len(dc_power) else 0
    sample_position = solar.iloc[best_index]
    sample_time = weather.index[best_index]
    return {
        "irradiance_source": source,
        "annual_irradiance_kwh_m2": round(float(weather["ghi"].sum() / 1000), 2),
        "solar_position": {
            "calculation": "PVLib",
            "sample_utc": sample_time.isoformat(),
            "elevation_deg": round(float(sample_position["apparent_elevation"]), 2),
            "azimuth_deg": round(float(sample_position["azimuth"]), 2),
        },
        "dc_power_w_estimate": round(float(np.max(dc_power)), 2),
        "ac_power_w_estimate": round(float(np.max(ac_power)), 2),
        "daily_energy_kwh_estimate": round(annual_energy / 365.25, 2),
        "monthly_energy_kwh_estimate": round(annual_energy / 12, 2),
        "annual_energy_kwh_estimate": round(annual_energy, 2),
        "specific_yield_kwh_per_kwp": round(annual_energy / capacity_kw, 2) if capacity_kw else 0,
        "energy_data_class": weather_note,
        "panel_model": model_metadata(),
        "panel_tilt_deg": settings.default_tilt,
        "panel_azimuth_deg": settings.default_azimuth,
        "system_losses_fraction": losses,
        "inverter_efficiency": settings.inverter_efficiency,
        "shading_assumption": "No roof-level or nearby-building shading data is available; panel shading factor is 1.0.",
    }


def _empty_estimate(source: str, weather_note: str) -> dict[str, Any]:
    return {
        "irradiance_source": source,
        "annual_irradiance_kwh_m2": 0,
        "solar_position": {"calculation": "PVLib", "sample_utc": None, "elevation_deg": None, "azimuth_deg": None},
        "dc_power_w_estimate": 0,
        "ac_power_w_estimate": 0,
        "daily_energy_kwh_estimate": 0,
        "monthly_energy_kwh_estimate": 0,
        "annual_energy_kwh_estimate": 0,
        "specific_yield_kwh_per_kwp": 0,
        "energy_data_class": weather_note,
        "panel_model": model_metadata(),
    }


@lru_cache(maxsize=256)
def _local_clearsky_weather(latitude: float, longitude: float) -> pd.DataFrame:
    """Cache one vectorized 8760-hour clear-sky series per rounded location."""
    times = pd.date_range("2023-01-01", "2024-01-01", freq="h", inclusive="left", tz="UTC")
    location = Location(latitude, longitude, tz="UTC")
    clear_sky = location.get_clearsky(times, model="ineichen")
    # Clear-sky weather has no cloud cover and is an upper-bound style estimate.
    return pd.DataFrame({
        "ghi": clear_sky["ghi"],
        "dni": clear_sky["dni"],
        "dhi": clear_sky["dhi"],
        "temp_air": 25.0,
        "wind_speed": 1.0,
    }, index=times)


def estimate_panel_annual_energy(
    latitude: float,
    longitude: float,
    panel_count: int,
    panel_power_w: float,
) -> dict[str, Any]:
    """Fast offline annual estimate; caller-visible source states that it is clear-sky modeled."""
    if panel_count <= 0 or panel_power_w <= 0:
        return _empty_estimate("not_required", "No panels fit this roof; annual generation is zero.")
    weather = _local_clearsky_weather(round(latitude, 2), round(longitude, 2))
    return _estimate_from_weather(
        weather,
        latitude,
        longitude,
        panel_count,
        panel_power_w,
        "pvlib_clear_sky",
        "PVLib clear-sky modeled estimate; clouds and measured site weather are not included.",
    )


@lru_cache(maxsize=64)
def _pvgis_tmy(latitude: float, longitude: float, api_url: str, timeout: float) -> pd.DataFrame:
    result = get_pvgis_tmy(
        latitude,
        longitude,
        outputformat="json",
        usehorizon=True,
        timeout=timeout,
        url=api_url,
    )
    return result[0]


async def estimate_panel_annual_energy_from_tmy(
    latitude: float,
    longitude: float,
    panel_count: int,
    panel_power_w: float,
) -> dict[str, Any]:
    """Estimate annual output from PVGIS historical typical-year weather, using the trained ML model."""
    if panel_count <= 0 or panel_power_w <= 0:
        return _empty_estimate("not_required", "No panels fit this roof; annual generation is zero.")
    latitude_key = round(latitude, 2)
    longitude_key = round(longitude, 2)
    try:
        weather = await asyncio.wait_for(
            asyncio.to_thread(
                _pvgis_tmy,
                latitude_key,
                longitude_key,
                settings.pvgis_api_url,
                settings.pvgis_timeout_seconds,
            ),
            timeout=settings.pvgis_timeout_seconds + 1,
        )
        return _estimate_from_weather(
            weather,
            latitude,
            longitude,
            panel_count,
            panel_power_w,
            "pvgis_tmy",
            "PVGIS typical meteorological year with PVLib transposition and the synthetic-trained ML power model; modeled annual output, not a live forecast or site survey.",
        )
    except Exception as exc:
        estimate = estimate_panel_annual_energy(latitude, longitude, panel_count, panel_power_w)
        estimate["weather_fallback_reason"] = type(exc).__name__
        estimate["energy_data_class"] = "PVLib clear-sky fallback; PVGIS weather was unavailable, so clouds and measured site weather are not included."
        return estimate
