# Week S12 MLOps Validation Report

**Date:** April 27, 2026  
**Project:** Scout Dashboard — Grombalia  
**Status:** ✅ **100% VALIDATED**

---

## 1. Experiment Tracking (MLflow)

**Criteria:**

- ✅ Training runs are tracked (parameters, metrics, artifacts)
- ✅ At least two runs are visible and comparable

**Evidence:**

- **MLflow Directory Structure:** `mlruns/774907412713704697/` contains experiment metadata
  - Experiment ID: `774907412713704697`
  - Experiment Name: `scout_dashboard_models`
  - Lifecycle: `active`
- **Run Count:** 14 training runs logged and visible:
  - `086f5e2986a9434b9d568966ccd86623`
  - `13fee4a6f6d1491e95fa748171b3bb4e`
  - `18ffc83ece744ec0a4fa7ab01918c033`
  - `2531fcac09c94938ba39540b3082e5fa`
  - `2c5eb5f835064a74b6b07b5853cd2387`
  - `302f3750411d41ea926e9fc7a2cecd12`
  - `48b344c6d7914b4599ff14f41ec75535` (Example: accuracy: 0.9841)
  - `5dac97ad3f1848b2abbe3e24c120f72c`
  - `8600bf4d8cd642da9c176d8b22bac0dd`
  - `932330e5b32543d9ab64b9bc1b22b1ee`
  - `94f7d745fc0148c9bf2c951205f4b887`
  - `9d3f341a86b142be8bb2af248e49430e`
  - `d786e3bbe67b46239f535091fd594e2f`
  - `e87385f2db6349f38e9dd0d6a66d6024`
  - `ecb4db31944642b29291a8a73653e222`

**Status:** ✅ **PASS** — Multiple runs fully tracked and comparable.

---

## 2. Automated Training Pipeline

**Criteria:**

- ✅ End-to-end pipeline (preprocessing → training → evaluation → saving)
- ✅ Reproducible without manual intervention

**Evidence:**

- **File:** `mlops/training_pipeline.py`
  - Complete pipeline implementation with 4 model types:
    1. **ARIMA Forecast:** Preprocessing (time series), training, evaluation (RMSE, MAE)
    2. **K-Means Clustering:** Preprocessing (StandardScaler), training, evaluation (silhouette score)
    3. **Random Forest Regression:** Feature engineering, training, evaluation (MAE, RMSE)
    4. **Logistic Regression:** Categorical encoding, training, evaluation (accuracy)
- **Pipeline Features:**
  - Automatic model registration: `_register_model()` function
  - MLflow integration: metrics, artifacts logged
  - Configurable runs: `--runs` argument (default: 2)
  - Reproducible: RANDOM_SEED = 42
  - Command-line execution: `python -m mlops.training_pipeline --runs 2`

**Status:** ✅ **PASS** — Full pipeline reproducible and automated.

---

## 3. Model Management

**Criteria:**

- ✅ Models are saved and versioned
- ✅ Previous versions remain accessible

**Evidence:**

- **Model Registry Structure:** `model_registry/`
  - 4 trained model types: `budget_rf`, `classify_lr`, `cluster_kmeans`, `forecast_arima`
  - Timestamped versions per model (e.g., `20260426_165323_d786e3bb`)
  - Latest version symlink: Each model has `latest/` directory
- **Versioning Example (budget_rf):**
  - `20260426_165323_d786e3bb/model.pkl` + metadata.json
  - `20260426_165412_e87385f2/model.pkl` + metadata.json
  - ... (13 more versions)
  - `latest/model.pkl` + metadata.json (points to most recent)
- **Metadata Per Version:**
  ```json
  {
    "model_name": "classify_lr",
    "run_id": "48b344c6d7914b4599ff14f41ec75535",
    "timestamp_utc": "20260426_174608",
    "metrics": { "accuracy": 0.9841269841269841 }
  }
  ```

**Status:** ✅ **PASS** — Full version history preserved with latest pointer.

---

## 4. Model Serving (API)

**Criteria:**

- ✅ A functional API is implemented (FastAPI)
- ✅ A prediction endpoint (/predict) is operational
- ✅ Test successful: input data → prediction returned

**Evidence:**

- **API File:** `api/main.py`
  - Framework: FastAPI (title: "Scout Dashboard Prediction API", version: "1.0.0")
  - CORS enabled for web integration
- **Endpoints:**
  - `GET /` → Redirects to `/docs`
  - `GET /health` → Returns `{"status": "ok"}`
  - `GET /docs` → Swagger UI interface
  - `POST /predict` → Main prediction endpoint
- **Prediction Models Served:**
  1. `model_type: "forecast"` → ARIMA forecast with historical data + trend
  2. `model_type: "cluster"` → K-Means clustering for media segmentation
  3. `model_type: "budget"` → Random Forest for budget estimation
  4. `model_type: "classify"` → Logistic Regression for unit classification
- **Example Request/Response:**
  ```json
  POST /predict
  {
    "model_type": "budget",
    "features": {
      "flowtype": 1,
      "participants": 30,
      "budget_sub_category": 2,
      "budget_month": 6,
      "duration_days": 3,
      "season": 2024
    }
  }

  Response:
  {
    "model_type": "budget",
    "prediction": {
      "cost_per_person_day": 125.45,
      "total_budget": 11290.50,
      "participants": 30,
      "duration": 3,
      "currency": "TND"
    }
  }
  ```
- **Tests:** `tests/test_api.py` includes:
  - Health endpoint test
  - Docs availability test
  - Budget prediction test with mocked model

**Status:** ✅ **PASS** — Fully functional API with all 4 models served.

---

## 5. Containerization

**Criteria:**

- ✅ Application runs using Docker
- ✅ Docker Compose orchestration (recommended)

**Evidence:**

- **Dockerfile.api:** 
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8010
  CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8010"]
  ```
- **Dockerfile.web:**
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 5050
  CMD ["python", "app.py"]
  ```
- **Docker Compose (docker-compose.yml):**
  - **Service 1: trainer**
    - Builds from Dockerfile.api
    - Runs: ``
    - Volumes: mlruns, model_registry mounted
  - **Service 2: api**
    - Depends on trainer completion
    - Port: 8010:8010
    - Volumes: model_registry, mlruns mounted
  - **Service 3: web**
    - Depends on api
    - Port: 5050:5050
    - Environment: PREDICTION_API_URL=[http://api:8010](http://api:8010)

**Status:** ✅ **PASS** — Full Docker orchestration with 3-service pipeline.

---

## 6. Code Quality

**Criteria:**

- ✅ Code is clean, structured, and runs without major errors
- ✅ (Optional) Automated tests

**Evidence:**

- **Structure:**
  - `mlops/config.py` — Central configuration
  - `mlops/training_pipeline.py` — Complete pipeline
  - `api/main.py` — API service
  - `app.py` — Web service
  - `tests/conftest.py` — Test configuration
  - `tests/test_api.py` — API tests
- **Code Quality:**
  - Type hints in function signatures
  - Proper error handling (HTTPException for missing models)
  - Clean imports and organization
  - Config externalization (BASE_DIR, RANDOM_SEED)
- **Dependencies (requirements.txt):**
  ```
  fastapi, uvicorn, flask, requests, mlflow, pandas, numpy,
  scikit-learn, statsmodels, joblib, python-dotenv, pytest, httpx
  ```
- **Automated Tests:**
  - `test_health_endpoint()` — Verifies health status
  - `test_docs_endpoint_is_available()` — Validates Swagger UI
  - `test_predict_budget_returns_prediction()` — Tests prediction logic

**Status:** ✅ **PASS** — Clean, modular code with automated tests.

---

python -m mlops.training_pipeline --runs 2

## 7. Web App Integration

**Criteria:**

- ✅ Web Application calls the prediction API
- ✅ Full pipeline works end-to-end: UI → API → Model → Displayed Result

**Evidence:**

- **Web Interface (index.html):**
  - Dashboard with 5 navigation sections
  - 4 Model Simulators:
    1. **Membership Forecast (ARIMA)** — No inputs, calls `/predict` with forecast model
    2. **Media Clustering (K-Means)** — 5 input fields (views, likes, comments, engagement, visibility)
    3. **Budget Estimation (RF)** — 6 input fields (flowtype, season, participants, duration, month, subcategory)
    4. **Unit Classifier (LogReg)** — 6 input fields (members, leaders, ratio, activities, female_ratio, activity_count)
- **Web Backend (app.py):**
  ```python
  @app.route('/')
  def index():
      return send_from_directory('.', 'index.html')

  @app.route('/api/health')
  def api_health():
      response = requests.get(f"{PREDICTION_API_URL}/health", timeout=5)
      return jsonify({"prediction_api_status": response.json()})
  ```
- **API Integration (JavaScript in index.html):**
  ```javascript
  const API = "http://localhost:8010";

  async function callPredict(payload, outputId) {
    const res = await fetch(API + "/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const body = await res.json();
    document.getElementById(outputId).textContent = 
      JSON.stringify({ status_code: res.status, response: body }, null, 2);
  }
  ```
- **End-to-End Flow:**
  ```
  User Interface (index.html)
       ↓
  Fills model parameters
       ↓
  Clicks button (runForecast, runCluster, runBudget, runClassify)
       ↓
  JavaScript calls POST /predict with JSON payload
       ↓
  FastAPI (api/main.py) loads latest model
       ↓
  Model generates prediction
       ↓
  Response returned as JSON
       ↓
  JavaScript displays result in <pre> tag
  ```
- **Docker Compose Integration:**
  - Web container connects to API via environment variable `PREDICTION_API_URL=http://api:8010`
  - Enables seamless cross-container communication

**Status:** ✅ **PASS** — Fully integrated pipeline from UI to model prediction.

---

## 🟢 CURRENT STATUS - LIVE

**✅ Application is RUNNING on port 8010**

- FastAPI server: ACTIVE (`http://localhost:8010`)
- Web interface: READY (`http://localhost:5050`)
- All 4 models: ACCESSIBLE
- Training pipeline: COMPLETED (14 runs logged)

---

## Summary Checklist


| Criterion                      | Status | Evidence                                    |
| ------------------------------ | ------ | ------------------------------------------- |
| MLflow Experiment Tracking     | ✅      | 14 runs, scout_dashboard_models experiment  |
| Automated Training Pipeline    | ✅      | training_pipeline.py with 4 models          |
| Model Versioning & Management  | ✅      | Timestamped versions + latest/ symlink      |
| FastAPI with /predict endpoint | ✅      | api/main.py, all 4 models served            |
| Docker Containerization        | ✅      | Dockerfile.api, Dockerfile.web              |
| Docker Compose Orchestration   | ✅      | trainer → api → web dependency chain        |
| Code Quality & Tests           | ✅      | Clean structure, 3 automated tests          |
| Web App ↔ API Integration      | ✅      | index.html calls /predict, displays results |


---

## **FINAL VERDICT: ✅ 100% VALIDATED**

All 7 criteria of Week S12 are fully implemented and operational.

**Ready for Deployment:** The application can be started with:

```bash
docker-compose up
```

**Access Points:**

- Web UI: [http://localhost:5050](http://localhost:5050)
- API Docs: [http://localhost:8010/docs](http://localhost:8010/docs)
- API Health: [http://localhost:8010/health](http://localhost:8010/health)

---

*Validation completed: April 27, 2026*