import json
import os
from pathlib import Path

import requests
import yaml
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder=".")

PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "http://localhost:8000")

# Comma-separated experiment folder names under ./mlruns (e.g. "774907412713704697" or "555555555").
# Empty = include all experiments except reserved dirs.
MLFLOW_EXPERIMENT_IDS = [
    x.strip()
    for x in os.getenv("MLFLOW_EXPERIMENT_IDS", "").split(",")
    if x.strip()
]

_SKIP_EXP_DIRS = frozenset({"models", ".trash"})


def _mlflow_status_name(raw) -> str:
    if isinstance(raw, str):
        return raw
    try:
        code = int(raw)
    except (TypeError, ValueError):
        return str(raw)
    return {
        1: "RUNNING",
        2: "SCHEDULED",
        3: "FINISHED",
        4: "FAILED",
        5: "KILLED",
    }.get(code, str(code))


def _read_mlflow_metric_files(metrics_dir: Path) -> dict:
    out = {}
    if not metrics_dir.is_dir():
        return out
    for path in metrics_dir.iterdir():
        if not path.is_file():
            continue
        try:
            lines = [
                ln.strip()
                for ln in path.read_text(encoding="utf-8").splitlines()
                if ln.strip()
            ]
            if not lines:
                continue
            parts = lines[-1].split()
            if len(parts) >= 2:
                val = float(parts[1])
                key = path.name
                out[key] = round(val, 8) if abs(val) < 1e6 else val
        except Exception as exc:
            print(f"Error reading metric file {path}: {exc}")
    return out


def _read_mlflow_sidecar_json(run_dir: Path, subfolder: str, filename: str) -> dict:
    p = run_dir / subfolder / filename
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error reading {p}: {exc}")
        return {}


def _read_mlflow_kv_dir(kv_dir: Path) -> dict:
    out = {}
    if not kv_dir.is_dir():
        return out
    for path in kv_dir.iterdir():
        if not path.is_file():
            continue
        try:
            out[path.name] = path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            print(f"Error reading {path}: {exc}")
    return out


def _collect_run_payload(run_dir: Path, exp_name: str) -> dict | None:
    meta_file = run_dir / "meta.yaml"
    if not meta_file.exists():
        return None
    try:
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error reading meta {meta_file}: {exc}")
        return None

    metrics = _read_mlflow_metric_files(run_dir / "metrics")
    metrics.update(_read_mlflow_sidecar_json(run_dir, "metrics", "metrics.json"))

    params = _read_mlflow_kv_dir(run_dir / "params")
    params.update(_read_mlflow_sidecar_json(run_dir, "params", "params.json"))

    tags = _read_mlflow_kv_dir(run_dir / "tags")
    tags.update(_read_mlflow_sidecar_json(run_dir, "tags", "tags.json"))

    start = meta.get("start_time")
    end = meta.get("end_time")
    duration_seconds = 0.0
    if start is not None and end is not None:
        duration_seconds = (end - start) / 1000.0

    status = _mlflow_status_name(meta.get("status"))

    run_name = tags.get("mlflow.runName") or meta.get("run_name") or ""

    return {
        "run_id": run_dir.name,
        "experiment_name": exp_name,
        "experiment_id": meta.get("experiment_id") or exp_name,
        "run_name": run_name,
        "status": status,
        "start_time": start,
        "end_time": end,
        "duration_seconds": duration_seconds,
        "metrics": metrics,
        "params": params,
        "tags": tags,
    }


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/mlflow")
def mlflow_page():
    """Technician-only UI: not linked from index.html. Bookmark e.g. http://localhost:5050/mlflow."""
    return send_from_directory(".", "mlflow.html")


@app.route("/api/health")
def api_health():
    try:
        response = requests.get(f"{PREDICTION_API_URL}/health", timeout=5)
        return jsonify({"prediction_api_status": response.json()})
    except Exception as exc:
        return jsonify({"prediction_api_status": "unreachable", "error": str(exc)}), 503


@app.route("/api/mlflow/runs")
def mlflow_runs():
    try:
        mlruns_path = Path("./mlruns")
        runs = []

        if not mlruns_path.exists():
            return jsonify({"runs": [], "total_runs": 0})

        allow = set(MLFLOW_EXPERIMENT_IDS) if MLFLOW_EXPERIMENT_IDS else None

        for exp_dir in mlruns_path.iterdir():
            if not exp_dir.is_dir() or exp_dir.name in _SKIP_EXP_DIRS:
                continue
            if allow is not None and exp_dir.name not in allow:
                continue

            exp_name = exp_dir.name
            for run_dir in exp_dir.iterdir():
                if not run_dir.is_dir() or run_dir.name in _SKIP_EXP_DIRS:
                    continue
                payload = _collect_run_payload(run_dir, exp_name)
                if payload:
                    runs.append(payload)

        runs.sort(key=lambda x: x["start_time"] or 0, reverse=True)

        return jsonify({"runs": runs, "total_runs": len(runs)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/model_registry")
def model_registry():
    try:
        registry_path = Path("./model_registry")
        models = []

        if not registry_path.exists():
            return jsonify({"models": []})

        for model_dir in registry_path.iterdir():
            if not model_dir.is_dir():
                continue
            latest_meta = model_dir / "latest" / "metadata.json"
            if latest_meta.exists():
                try:
                    metadata = json.loads(latest_meta.read_text(encoding="utf-8"))
                    models.append(
                        {
                            "model_name": model_dir.name,
                            "version": "latest",
                            "metadata": metadata,
                        }
                    )
                except Exception as e:
                    print(f"Error reading metadata for {model_dir.name}: {e}")

        return jsonify({"models": models})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(debug=True, port=5050)
