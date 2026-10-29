"""Generate reproducible PVLib-based synthetic panel-power training samples.

The weather and panel examples are simulated. They are not measured site data.
Run with Backend/.venv Python; output is written to the repository root.
"""
from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from pvlib import irradiance, pvsystem, temperature
from pvlib.location import Location

SITES = [
    ("site_00", -33.87, 151.21),
    ("site_01", -23.55, -46.63),
    ("site_02", -1.29, 36.82),
    ("site_03", 13.08, 80.27),
    ("site_04", 19.08, 72.88),
    ("site_05", 28.61, 77.21),
    ("site_06", 30.04, 31.24),
    ("site_07", 40.71, -74.01),
    ("site_08", 51.50, -0.12),
    ("site_09", 35.68, 139.69),
]
SAMPLES_PER_SITE = 1_200
RANDOM_SEED = 2026
PANEL_TEMPERATURE_COEFFICIENT = -0.0035
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "synthetic_solar_data.csv"

FIELDS = [
    "sample_id", "site_id", "latitude", "longitude", "day_of_year", "hour_utc",
    "solar_zenith_deg", "solar_azimuth_deg", "roof_tilt_deg", "roof_azimuth_deg",
    "ghi_w_m2", "dni_w_m2", "dhi_w_m2", "cloud_factor", "shade_factor",
    "poa_w_m2", "effective_poa_w_m2", "air_temperature_c", "wind_speed_m_s",
    "cell_temperature_c", "panel_area_m2", "panel_efficiency", "panel_rated_power_w",
    "panel_power_w",
]


def generate_site_rows(site_id: str, latitude: float, longitude: float, count: int, rng: np.random.Generator) -> list[dict[str, object]]:
    days = rng.integers(1, 366, count)
    hours = rng.integers(4, 21, count)
    times = pd.DatetimeIndex([
        pd.Timestamp("2023-01-01", tz="UTC") + timedelta(days=int(day - 1), hours=int(hour))
        for day, hour in zip(days, hours)
    ])
    location = Location(latitude, longitude, tz="UTC")
    solar = location.get_solarposition(times)
    clear_sky = location.get_clearsky(times, model="ineichen")

    cloud = rng.uniform(0.45, 1.0, count)
    ghi = clear_sky["ghi"].to_numpy() * cloud
    dni = clear_sky["dni"].to_numpy() * cloud
    dhi = clear_sky["dhi"].to_numpy() * cloud
    tilt = rng.uniform(0, 45, count)
    azimuth = rng.uniform(0, 360, count)
    poa = irradiance.get_total_irradiance(
        tilt, azimuth, solar["apparent_zenith"].to_numpy(), solar["azimuth"].to_numpy(),
        dni, ghi, dhi, albedo=0.2,
    )["poa_global"]
    poa = np.asarray(poa, dtype=float)

    area = rng.uniform(1.6, 2.8, count)
    efficiency = rng.uniform(0.17, 0.24, count)
    rated_power = area * 1000 * efficiency
    cloud_shadow = rng.uniform(0.35, 0.8, count)
    shade = np.where(rng.random(count) < 0.88, rng.beta(14, 1.5, count), cloud_shadow)
    effective_poa = np.maximum(0, poa * shade)

    seasonal_phase = 172 if latitude >= 0 else 355
    seasonal = np.cos(2 * np.pi * (days - seasonal_phase) / 365)
    seasonal_air = 23 - 0.12 * abs(latitude) + 10 * seasonal
    air_temperature = np.clip(seasonal_air + rng.normal(0, 5, count), -15, 45)
    wind_speed = rng.uniform(0.3, 8.0, count)
    cell_temperature = temperature.faiman(effective_poa, air_temperature, wind_speed)
    power = pvsystem.pvwatts_dc(
        effective_poa, cell_temperature, rated_power,
        PANEL_TEMPERATURE_COEFFICIENT,
    )

    rounded_time = times.hour + times.minute / 60
    return [
        {
            "sample_id": f"{site_id}-{i:05d}",
            "site_id": site_id,
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "day_of_year": int(days[i]),
            "hour_utc": round(float(rounded_time[i]), 2),
            "solar_zenith_deg": round(float(solar["apparent_zenith"].iloc[i]), 4),
            "solar_azimuth_deg": round(float(solar["azimuth"].iloc[i]), 4),
            "roof_tilt_deg": round(float(tilt[i]), 3),
            "roof_azimuth_deg": round(float(azimuth[i]), 3),
            "ghi_w_m2": round(float(ghi[i]), 3),
            "dni_w_m2": round(float(dni[i]), 3),
            "dhi_w_m2": round(float(dhi[i]), 3),
            "cloud_factor": round(float(cloud[i]), 4),
            "shade_factor": round(float(shade[i]), 4),
            "poa_w_m2": round(float(poa[i]), 3),
            "effective_poa_w_m2": round(float(effective_poa[i]), 3),
            "air_temperature_c": round(float(air_temperature[i]), 3),
            "wind_speed_m_s": round(float(wind_speed[i]), 3),
            "cell_temperature_c": round(float(cell_temperature[i]), 3),
            "panel_area_m2": round(float(area[i]), 3),
            "panel_efficiency": round(float(efficiency[i]), 4),
            "panel_rated_power_w": round(float(rated_power[i]), 3),
            "panel_power_w": round(float(power[i]), 4),
        }
        for i in range(count)
    ]


def generate_dataset(samples_per_site: int = SAMPLES_PER_SITE, seed: int = RANDOM_SEED) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for site_id, latitude, longitude in SITES:
        rows.extend(generate_site_rows(site_id, latitude, longitude, samples_per_site, rng))
    return rows


def save_dataset(rows: list[dict[str, object]], path: Path = OUTPUT_PATH) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} simulated samples to {path}")


if __name__ == "__main__":
    save_dataset(generate_dataset())
