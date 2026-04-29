from fastapi.testclient import TestClient

from api import main


client = TestClient(main.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_endpoint_is_available():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_predict_budget_returns_prediction(monkeypatch):
    class DummyModel:
        def predict(self, x):
            return [1.0]

    def _fake_load_latest(model_key):
        assert model_key == "budget_rf"
        return DummyModel()

    monkeypatch.setattr(main, "_load_latest", _fake_load_latest)
    payload = {
        "model_type": "budget",
        "features": {
            "flowtype": 1,
            "participants": 30,
            "budget_sub_category": 2,
            "budget_month": 6,
            "duration_days": 3,
            "season": 2024,
        },
    }
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "budget"
    assert "prediction" in body
    assert "total_budget" in body["prediction"]

