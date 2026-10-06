from services.pv_service import estimate_panel_annual_energy


def test_solar_estimate_is_explicitly_synthetic():
    result = estimate_panel_annual_energy(19, 72, 4, 400)
    assert result["annual_energy_kwh_estimate"] > 0
    assert result["irradiance_source"] == "synthetic_demo"
    assert result["energy_data_class"].startswith("estimated")
