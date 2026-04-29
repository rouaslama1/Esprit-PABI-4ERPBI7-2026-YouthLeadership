import argparse
import json
from datetime import datetime
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.arima.model import ARIMA

from mlops.config import MLRUNS_DIR, MODEL_REGISTRY_DIR, RANDOM_SEED


def _register_model(model_name: str, model_obj, run_id: str, metrics: dict) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    version_dir = MODEL_REGISTRY_DIR / model_name / f"{timestamp}_{run_id[:8]}"
    version_dir.mkdir(parents=True, exist_ok=True)

    model_path = version_dir / "model.pkl"
    metadata_path = version_dir / "metadata.json"
    joblib.dump(model_obj, model_path)

    metadata = {
        "model_name": model_name,
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "metrics": metrics,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    latest_dir = MODEL_REGISTRY_DIR / model_name / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_obj, latest_dir / "model.pkl")
    (latest_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return version_dir


def train_forecast_model():
    values = np.array([163.0, 97.0, 83.0], dtype=float)
    train = values[:2]
    test = values[2:]

    model = ARIMA(train, order=(0, 0, 0)).fit()
    pred = model.forecast(steps=1)
    rmse = float(np.sqrt(mean_squared_error(test, pred)))
    mae = float(mean_absolute_error(test, pred))
    metrics = {"rmse": rmse, "mae": mae}
    return model, metrics


def train_cluster_model():
    rng = np.random.default_rng(RANDOM_SEED)
    low = rng.normal(loc=[4000, 180, 12, 0.03, 0.20], scale=[600, 60, 4, 0.01, 0.06], size=(40, 5))
    high = rng.normal(loc=[12000, 900, 80, 0.12, 0.65], scale=[1000, 120, 18, 0.02, 0.09], size=(15, 5))
    x = np.vstack([low, high])

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=2, random_state=RANDOM_SEED, n_init=10)),
        ]
    )
    labels = pipeline.fit_predict(x)
    transformed = pipeline.named_steps["scaler"].transform(x)
    sil = float(silhouette_score(transformed, labels))
    return pipeline, {"silhouette_score": sil}


def train_budget_model():
    rng = np.random.default_rng(RANDOM_SEED)
    n = 400
    flowtype = rng.integers(1, 3, size=n)
    participants = rng.integers(10, 120, size=n)
    budget_sub_category = rng.integers(1, 6, size=n)
    budget_month = rng.integers(1, 13, size=n)
    duration_days = rng.integers(1, 10, size=n)
    season = rng.integers(2023, 2027, size=n)

    x = np.column_stack([flowtype, participants, budget_sub_category, budget_month, duration_days, season])
    y = (
        4.0
        + 0.015 * participants
        + 0.2 * duration_days
        + 0.35 * budget_sub_category
        + 0.03 * (season - 2023)
        + rng.normal(0, 0.6, size=n)
    )
    y = np.maximum(y, 0.2)
    y_log = np.log1p(y)

    x_train, x_test, y_train, y_test = train_test_split(x, y_log, test_size=0.2, random_state=RANDOM_SEED)
    model = RandomForestRegressor(n_estimators=250, random_state=RANDOM_SEED)
    model.fit(x_train, y_train)
    preds = model.predict(x_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))
    return model, {"rmse_log": rmse, "mae_log": mae}


def train_classifier_model():
    rng = np.random.default_rng(RANDOM_SEED)
    n = 250
    members_count = rng.integers(15, 150, size=n)
    leaders_count = np.clip((members_count * rng.uniform(0.05, 0.15, size=n)).astype(int), 1, None)
    ratio = leaders_count / np.maximum(members_count, 1)
    activities_per_member = rng.uniform(0.5, 5.0, size=n)
    female_ratio = rng.uniform(0.2, 0.7, size=n)
    activity_count = np.maximum((activities_per_member * members_count / 10).astype(int), 1)

    x = np.column_stack(
        [members_count, leaders_count, ratio, activities_per_member, female_ratio, activity_count]
    )
    score = activities_per_member + 0.6 * ratio + 0.02 * leaders_count
    y = np.digitize(score, bins=np.quantile(score, [0.33, 0.66]))

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )
    model = LogisticRegression(max_iter=1000)
    model.fit(x_train, y_train)
    preds = model.predict(x_test)
    acc = float(accuracy_score(y_test, preds))
    return model, {"accuracy": acc}


def run_training(run_name: str):
    tracking_uri = MLRUNS_DIR.resolve().as_uri()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("scout_dashboard_models")

    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        mlflow.log_param("random_seed", RANDOM_SEED)

        forecast_model, forecast_metrics = train_forecast_model()
        cluster_model, cluster_metrics = train_cluster_model()
        budget_model, budget_metrics = train_budget_model()
        classifier_model, classifier_metrics = train_classifier_model()

        all_metrics = {}
        for k, v in forecast_metrics.items():
            all_metrics[f"forecast_{k}"] = v
        for k, v in cluster_metrics.items():
            all_metrics[f"cluster_{k}"] = v
        for k, v in budget_metrics.items():
            all_metrics[f"budget_{k}"] = v
        for k, v in classifier_metrics.items():
            all_metrics[f"classifier_{k}"] = v
        mlflow.log_metrics(all_metrics)

        _register_model("forecast_arima", forecast_model, run_id, forecast_metrics)
        _register_model("cluster_kmeans", cluster_model, run_id, cluster_metrics)
        _register_model("budget_rf", budget_model, run_id, budget_metrics)
        _register_model("classify_lr", classifier_model, run_id, classifier_metrics)

        mlflow.sklearn.log_model(cluster_model, artifact_path="cluster_kmeans")
        mlflow.sklearn.log_model(budget_model, artifact_path="budget_rf")
        mlflow.sklearn.log_model(classifier_model, artifact_path="classify_lr")

        # statsmodels ARIMA object is stored as artifact file
        tmp_dir = Path("artifacts_tmp")
        tmp_dir.mkdir(exist_ok=True)
        arima_path = tmp_dir / "forecast_arima.pkl"
        joblib.dump(forecast_model, arima_path)
        mlflow.log_artifact(str(arima_path), artifact_path="forecast_arima")
        arima_path.unlink(missing_ok=True)
        tmp_dir.rmdir()

        print(f"Training run completed. run_id={run_id}")


def main():
    parser = argparse.ArgumentParser(description="Run automated MLOps training pipeline.")
    parser.add_argument("--runs", type=int, default=2, help="Number of runs to execute (default: 2).")
    args = parser.parse_args()

    MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    for i in range(args.runs):
        run_training(run_name=f"pipeline_run_{i + 1}")


if __name__ == "__main__":
    main()
