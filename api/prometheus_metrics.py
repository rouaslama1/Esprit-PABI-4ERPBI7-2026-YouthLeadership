"""
Prometheus metrics for Scout prediction API (Week S13 monitoring).
"""
from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

# --- Traffic & stability ---
HTTP_REQUESTS = Counter(
    "scout_http_requests_total",
    "HTTP requests by route family and status class",
    ["method", "route", "status_class"],
)

HTTP_ERRORS = Counter(
    "scout_http_errors_total",
    "HTTP error responses (4xx/5xx)",
    ["route", "status_code"],
)

PREDICTIONS_TOTAL = Counter(
    "scout_predictions_total",
    "Successful predictions by model type",
    ["model_type"],
)

PREDICTION_ERRORS = Counter(
    "scout_prediction_errors_total",
    "Failed predictions",
    ["model_type", "error_kind"],
)

PREDICTION_LATENCY = Histogram(
    "scout_prediction_latency_seconds",
    "Latency of POST /predict by model",
    ["model_type"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

# HTTP-level slow /predict (middleware; complements histogram for alerting)
SLOW_PREDICT_HTTP_TOTAL = Counter(
    "scout_slow_predict_http_total",
    "POST /predict responses slower than HTTP middleware threshold (seconds)",
)

# --- Model health vs baseline (dimensionless; 1.0 = nominal) ---
MODEL_HEALTH_RATIO = Gauge(
    "scout_model_health_vs_baseline_ratio",
    "Health vs training baseline proxy.",
    ["model_type"],
)

CLASSIFIER_CONFIDENCE = Gauge(
    "scout_classifier_max_confidence_ratio",
    "Max class probability on last classify call (0–1).",
)

CLASSIFIER_CONFIDENCE_BASELINE = Gauge(
    "scout_classifier_confidence_baseline_static",
    "Reference baseline (uniform 3-class).",
)

BASELINE_ACCURACY_PROXY = Gauge(
    "scout_baseline_accuracy_proxy",
    "Static baseline accuracy proxy from training metadata.",
    ["model_type"],
)

# --- Data quality ---
DATA_VALIDATION_ERRORS = Counter(
    "scout_data_validation_errors_total",
    "Missing/invalid feature payloads",
    ["model_type"],
)

FEATURE_COMPLETENESS_RATIO = Gauge(
    "scout_feature_completeness_ratio",
    "1.0 when all required features present.",
    ["model_type"],
)

LAST_SUCCESS_UNIX = Gauge(
    "scout_last_success_unix_timestamp",
    "Unix time of last successful prediction (freshness; use time()-metric in Grafana).",
    ["model_type"],
)

# --- Drift flags (simple thresholds) ---
DRIFT_DETECTED = Gauge(
    "scout_drift_detected",
    "1 if degradation rule fired on last classify/budget path.",
    ["kind"],
)


def route_family(path: str) -> str:
    if path.startswith("/predict"):
        return "/predict"
    if path.startswith("/health"):
        return "/health"
    if path.startswith("/metrics"):
        return "/metrics"
    if path.startswith("/docs") or path.startswith("/openapi"):
        return "/docs"
    return "/other"


def status_class(code: int) -> str:
    if code < 400:
        return "2xx"
    if code < 500:
        return "4xx"
    return "5xx"


def observe_http(method: str, path: str, status_code: int) -> None:
    rf = route_family(path)
    HTTP_REQUESTS.labels(method, rf, status_class(status_code)).inc()
    if status_code >= 400:
        HTTP_ERRORS.labels(rf, str(status_code)).inc()


def init_baselines() -> None:
    CLASSIFIER_CONFIDENCE_BASELINE.set(1 / 3)
    BASELINE_ACCURACY_PROXY.labels("forecast").set(0.92)
    BASELINE_ACCURACY_PROXY.labels("cluster").set(0.84)
    BASELINE_ACCURACY_PROXY.labels("budget").set(0.94)
    BASELINE_ACCURACY_PROXY.labels("classify").set(0.98)
    for m in ("forecast", "cluster", "budget", "classify"):
        MODEL_HEALTH_RATIO.labels(m).set(1.0)
        FEATURE_COMPLETENESS_RATIO.labels(m).set(1.0)
        LAST_SUCCESS_UNIX.labels(m).set(0)
    for k in ("confidence_drop", "accuracy_proxy", "latency"):
        DRIFT_DETECTED.labels(k).set(0.0)


def record_validation_error(model_type: str, kind: str = "missing_features") -> None:
    DATA_VALIDATION_ERRORS.labels(model_type).inc()
    PREDICTION_ERRORS.labels(model_type, kind).inc()
    FEATURE_COMPLETENESS_RATIO.labels(model_type).set(0.0)


def record_success(
    model_type: str,
    latency_s: float,
    *,
    classify_probs: dict[str, float] | None = None,
    simulate_drift: bool = False,
) -> None:
    PREDICTION_LATENCY.labels(model_type).observe(latency_s)
    PREDICTIONS_TOTAL.labels(model_type).inc()
    FEATURE_COMPLETENESS_RATIO.labels(model_type).set(1.0)
    now = time.time()
    LAST_SUCCESS_UNIX.labels(model_type).set(now)

    if model_type == "classify" and classify_probs:
        vals = list(classify_probs.values())
        max_p = max(vals) / 100.0 if max(vals) > 1.0 else max(vals)
        if simulate_drift:
            max_p *= 0.55
        CLASSIFIER_CONFIDENCE.set(max_p)
        uniform = 1 / 3
        MODEL_HEALTH_RATIO.labels("classify").set(min(max_p / uniform, 1.2) / 1.2)
        # >5% drop vs previous implied baseline (0.35 heuristic when healthy)
        baseline_heuristic = 0.35
        confidence_drop = max_p < baseline_heuristic * 0.95
        DRIFT_DETECTED.labels("confidence_drop").set(1.0 if (simulate_drift or confidence_drop) else 0.0)
        DRIFT_DETECTED.labels("accuracy_proxy").set(1.0 if simulate_drift else 0.0)
    else:
        MODEL_HEALTH_RATIO.labels(model_type).set(1.0 if not simulate_drift else 0.72)
        if simulate_drift:
            DRIFT_DETECTED.labels("accuracy_proxy").set(1.0)


def record_latency_drift(elapsed: float, threshold: float = 1.5) -> None:
    slow = elapsed > threshold
    DRIFT_DETECTED.labels("latency").set(1.0 if slow else 0.0)
    if slow:
        SLOW_PREDICT_HTTP_TOTAL.inc()
