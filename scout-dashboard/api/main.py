from pathlib import Path
from typing import Any, Dict, Literal

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_REGISTRY_DIR = BASE_DIR / "model_registry"

app = FastAPI(title="Scout Dashboard Prediction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5050", "http://127.0.0.1:5050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"model_type": "forecast", "features": {}},
                {
                    "model_type": "budget",
                    "features": {
                        "flowtype": 1,
                        "participants": 30,
                        "budget_sub_category": 2,
                        "budget_month": 6,
                        "duration_days": 3,
                        "season": 2024,
                    },
                },
                {
                    "model_type": "cluster",
                    "features": {
                        "views": 5000,
                        "likes": 300,
                        "comments": 20,
                        "engagement_rate": 0.065,
                        "visibility_index": 0.30,
                    },
                },
                {
                    "model_type": "classify",
                    "features": {
                        "members_count": 30,
                        "leaders_count": 3,
                        "leaders_to_members_ratio": 0.10,
                        "activities_per_member": 2.5,
                        "female_ratio": 0.40,
                        "activity_count": 10,
                    },
                },
            ]
        }
    )
    model_type: Literal["forecast", "cluster", "budget", "classify"]
    features: Dict[str, float] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    model_type: str
    prediction: Dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_type": "budget",
                "prediction": {
                    "cost_per_person_day": 12.34,
                    "total_budget": 1110.6,
                    "participants": 30,
                    "duration": 3,
                    "currency": "TND"
                }
            }
        }
    )


def _load_latest(model_key: str):
    model_path = MODEL_REGISTRY_DIR / model_key / "latest" / "model.pkl"
    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_key}' not found. Run training pipeline first.",
        )
    return joblib.load(model_path)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    if payload.model_type == "forecast":
        model = _load_latest("forecast_arima")
        forecast_val = float(model.forecast(steps=1)[0])
        response = {
            "forecast": round(forecast_val),
            "historical": [163, 97, 83],
            "trend": "Recovery expected" if forecast_val > 83 else "Continued decline",
            "change_pct": round(((forecast_val - 83) / 83) * 100, 1),
        }
        return PredictResponse(model_type=payload.model_type, prediction=response)

    if payload.model_type == "cluster":
        required_keys = ["views", "likes", "comments", "engagement_rate", "visibility_index"]
        if not all(k in payload.features for k in required_keys):
            raise HTTPException(status_code=400, detail=f"Missing required features for {payload.model_type}: {required_keys}")
        model = _load_latest("cluster_kmeans")
        f = payload.features
        x = np.array(
            [[f["views"], f["likes"], f["comments"], f["engagement_rate"], f["visibility_index"]]]
        )
        label = int(model.predict(x)[0])
        cluster_names = {0: "Low Visibility", 1: "High Visibility"}
        cluster_desc = {
            0: "Standard performance. Focus on content quality and posting frequency to grow.",
            1: "Viral / High-Reach content. Maintain strategy and replicate winning formats.",
        }
        response = {
            "cluster": label,
            "cluster_name": cluster_names.get(label, f"Cluster {label}"),
            "description": cluster_desc.get(label, ""),
            "recommendation": "Target Cluster 1 strategy" if label == 0 else "You are already in the top cluster!",
        }
        return PredictResponse(model_type=payload.model_type, prediction=response)

    if payload.model_type == "budget":
        required_keys = ["flowtype", "participants", "budget_sub_category", "budget_month", "duration_days", "season"]
        if not all(k in payload.features for k in required_keys):
            raise HTTPException(status_code=400, detail=f"Missing required features for {payload.model_type}: {required_keys}")
        model = _load_latest("budget_rf")
        f = payload.features
        x = np.array(
            [
                [
                    f["flowtype"],
                    f["participants"],
                    f["budget_sub_category"],
                    f["budget_month"],
                    f["duration_days"],
                    f["season"],
                ]
            ]
        )
        log_pred = float(model.predict(x)[0])
        cost_per_person_day = float(np.expm1(log_pred))
        participants = float(f["participants"])
        duration = float(f["duration_days"])
        response = {
            "cost_per_person_day": round(cost_per_person_day, 2),
            "total_budget": round(cost_per_person_day * participants * duration, 2),
            "participants": int(participants),
            "duration": int(duration),
            "currency": "TND",
        }
        return PredictResponse(model_type=payload.model_type, prediction=response)

    if payload.model_type == "classify":
        required_keys = ["members_count", "leaders_count", "leaders_to_members_ratio", "activities_per_member", "female_ratio", "activity_count"]
        if not all(k in payload.features for k in required_keys):
            raise HTTPException(status_code=400, detail=f"Missing required features for {payload.model_type}: {required_keys}")
        model = _load_latest("classify_lr")
        f = payload.features
        x = np.array(
            [
                [
                    f["members_count"],
                    f["leaders_count"],
                    f["leaders_to_members_ratio"],
                    f["activities_per_member"],
                    f["female_ratio"],
                    f["activity_count"],
                ]
            ]
        )
        pred = int(model.predict(x)[0])
        proba = model.predict_proba(x)[0].tolist()
        level_map = {0: "Low", 1: "Medium", 2: "High"}
        color_map = {0: "#E74C3C", 1: "#F39C12", 2: "#27AE60"}
        advice_map = {
            0: "Unit needs urgent support. Consider increasing leader-to-member ratio and scheduling more structured activities.",
            1: "Unit shows moderate engagement. Focus on retention and activity diversity to reach High level.",
            2: "Unit is performing excellently. Share best practices with other units.",
        }
        response = {
            "level": pred,
            "level_name": level_map[pred],
            "color": color_map[pred],
            "probabilities": {level_map[i]: round(float(p) * 100, 1) for i, p in enumerate(proba)},
            "advice": advice_map[pred],
        }
        return PredictResponse(model_type=payload.model_type, prediction=response)

    raise HTTPException(status_code=400, detail=f"Unsupported model_type: {payload.model_type}")
