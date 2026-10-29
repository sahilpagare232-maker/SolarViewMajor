"""Fit and validate a small ML surrogate on PVLib-generated synthetic samples."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "synthetic_solar_data.csv"
MODEL_PATH = Path(__file__).resolve().parent / "solar_power_model.json"
HELD_OUT_SITES = {"site_08", "site_09"}


def make_features(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    poa = np.array([float(row["effective_poa_w_m2"]) for row in rows])
    temperature = np.array([float(row["cell_temperature_c"]) for row in rows])
    rated_power = np.array([float(row["panel_rated_power_w"]) for row in rows])
    irradiance_power = rated_power * np.maximum(poa, 0) / 1000
    temperature_interaction = irradiance_power * (temperature - 25)
    target = np.array([float(row["panel_power_w"]) for row in rows])
    features = np.column_stack((irradiance_power, temperature_interaction))
    return features, target, [row["site_id"] for row in rows]


def fit_and_validate(dataset_path: Path = DATASET, model_path: Path = MODEL_PATH) -> dict[str, object]:
    with dataset_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    features, target, site_ids = make_features(rows)
    validation_mask = np.array([site_id in HELD_OUT_SITES for site_id in site_ids])
    train_mask = ~validation_mask
    if not train_mask.any() or not validation_mask.any():
        raise ValueError("Training data must include both training and held-out sites.")

    center = np.median(features[train_mask], axis=0)
    scale = np.percentile(features[train_mask], 75, axis=0) - np.percentile(features[train_mask], 25, axis=0)
    scale = np.where(scale > 1e-9, scale, 1.0)
    normalized = (features - center) / scale
    design = np.column_stack((np.ones(len(rows)), normalized))
    coefficients, *_ = np.linalg.lstsq(design[train_mask], target[train_mask], rcond=None)
    predictions = np.maximum(design[validation_mask] @ coefficients, 0)
    actual = target[validation_mask]
    errors = predictions - actual
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    denominator = float(np.sum((actual - np.mean(actual)) ** 2))
    r2 = 1 - float(np.sum(errors**2)) / denominator if denominator else 1.0

    model: dict[str, object] = {
        "model_name": "synthetic solar power linear regressor",
        "model_version": 1,
        "target": "instantaneous DC panel power in watts",
        "features": ["rated_power_times_effective_poa", "irradiance_temperature_interaction"],
        "feature_center": center.tolist(),
        "feature_scale": scale.tolist(),
        "coefficients": coefficients.tolist(),
        "temperature_coefficient": -0.0035,
        "training_samples": int(train_mask.sum()),
        "validation_samples": int(validation_mask.sum()),
        "held_out_sites": sorted(HELD_OUT_SITES),
        "validation_metrics": {"mae_w": mae, "rmse_w": rmse, "r2": r2},
        "training_data_class": "PVLib clear-sky model with synthetic cloud, shade, temperature, and panel variations; not measured generation data",
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    return model


if __name__ == "__main__":
    result = fit_and_validate()
    metrics = result["validation_metrics"]
    print(
        f"Trained on {result['training_samples']:,}; held out {result['validation_samples']:,} samples "
        f"from sites {', '.join(result['held_out_sites'])}: "
        f"MAE={metrics['mae_w']:.4f} W, RMSE={metrics['rmse_w']:.4f} W, R²={metrics['r2']:.6f}"
    )
    print(f"Model saved to {MODEL_PATH}")
