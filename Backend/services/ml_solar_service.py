"""Runtime inference for the small PVLib-trained synthetic solar power model."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "solar_power_model.json"


@lru_cache(maxsize=1)
def _load_model() -> dict[str, object]:
    with MODEL_PATH.open(encoding="utf-8") as model_file:
        return json.load(model_file)


def model_metadata() -> dict[str, object]:
    model = _load_model()
    return {
        "name": model["model_name"],
        "version": model["model_version"],
        "validation_metrics": model["validation_metrics"],
        "training_data_class": model["training_data_class"],
    }


def predict_dc_power_w(effective_poa_w_m2: object, cell_temperature_c: object, rated_power_w: float) -> np.ndarray:
    """Predict DC power and constrain it to physically plausible panel limits."""
    model = _load_model()
    poa = np.asarray(effective_poa_w_m2, dtype=float)
    cell_temperature = np.asarray(cell_temperature_c, dtype=float)
    base_power = max(0.0, float(rated_power_w)) * np.maximum(poa, 0) / 1000
    features = np.stack((base_power, base_power * (cell_temperature - 25)), axis=-1)
    center = np.asarray(model["feature_center"], dtype=float)
    scale = np.asarray(model["feature_scale"], dtype=float)
    coefficients = np.asarray(model["coefficients"], dtype=float)
    design = np.concatenate((np.ones((*features.shape[:-1], 1)), (features - center) / scale), axis=-1)
    prediction = design @ coefficients
    return np.clip(prediction, 0, max(0.0, float(rated_power_w)) * 1.2)
