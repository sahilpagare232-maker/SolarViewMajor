import numpy as np
import pandas as pd
import pytest
from pvlib.pvsystem import pvwatts_dc

from services.ml_solar_service import model_metadata, predict_dc_power_w
from services.pv_service import estimate_panel_annual_energy, estimate_panel_annual_energy_from_tmy


def test_clear_sky_estimate_is_labeled_and_nonzero():
    result = estimate_panel_annual_energy(19, 72, 4, 400)

    assert result["annual_energy_kwh_estimate"] > 0
    assert result["irradiance_source"] == "pvlib_clear_sky"
    assert "clear-sky" in result["energy_data_class"]
    assert result["panel_model"]["name"] == "synthetic solar power linear regressor"
    assert result["specific_yield_kwh_per_kwp"] > 0


def test_ml_model_matches_held_out_pvwatts_power_range():
    poa = np.array([0, 250, 700, 1000], dtype=float)
    cell_temperature = np.array([20, 35, 45, 60], dtype=float)
    predicted = predict_dc_power_w(poa, cell_temperature, 400)
    expected = pvwatts_dc(poa, cell_temperature, 400, -0.0035)

    assert np.max(np.abs(predicted - expected)) < 0.01
    assert model_metadata()["validation_metrics"]["r2"] > 0.999


@pytest.mark.asyncio
async def test_tmy_estimate_uses_cached_weather_and_ml_power_model(monkeypatch):
    times = pd.date_range("2023-06-21 08:00", periods=5, freq="h", tz="UTC")
    weather = pd.DataFrame({
        "ghi": [150, 350, 550, 700, 650],
        "dni": [100, 250, 450, 600, 500],
        "dhi": [50, 100, 100, 100, 150],
        "temp_air": [24, 26, 29, 31, 30],
        "wind_speed": [1.0, 1.5, 2.0, 2.0, 1.5],
    }, index=times)
    monkeypatch.setattr("services.pv_service._pvgis_tmy", lambda *_args: weather)

    result = await estimate_panel_annual_energy_from_tmy(19, 72, 3, 400)

    assert result["irradiance_source"] == "pvgis_tmy"
    assert result["annual_energy_kwh_estimate"] > 0
    assert "PVGIS typical meteorological year" in result["energy_data_class"]
    assert result["panel_model"]["validation_metrics"]["r2"] > 0.999


@pytest.mark.asyncio
async def test_tmy_failure_falls_back_to_labeled_clear_sky(monkeypatch):
    def unavailable(*_args):
        raise TimeoutError("unavailable")

    monkeypatch.setattr("services.pv_service._pvgis_tmy", unavailable)
    result = await estimate_panel_annual_energy_from_tmy(19, 72, 1, 400)

    assert result["irradiance_source"] == "pvlib_clear_sky"
    assert "fallback" in result["energy_data_class"]
    assert result["weather_fallback_reason"] == "TimeoutError"
