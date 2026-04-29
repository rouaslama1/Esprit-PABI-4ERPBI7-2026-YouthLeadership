# Scout Dashboard - S12 MLOps

This project industrializes your 4 best models with:
- MLflow experiment tracking
- Automated training pipeline
- Local model registry with versioning
- FastAPI serving with `/predict`
- Minimal Flask web page to verify prediction API call
- Docker and Docker Compose deployment

## Project structure

`api/main.py`: FastAPI serving (`/health`, `/predict`)  
`mlops/training_pipeline.py`: end-to-end automated training + MLflow logging + model versioning  
`app.py`: Flask web page server (serves `index.html`)  
`index.html`: minimal page to verify FastAPI `/predict` call  
`model_registry/`: saved and versioned models (auto-generated)  
`mlruns/`: MLflow tracked runs (auto-generated)  
`docker-compose.yml`: multi-service orchestration (trainer + API + web)  

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Run automated training pipeline (MLflow + model versioning)

This command executes two runs by default (for comparison in MLflow):

```bash
python -m mlops.training_pipeline --runs 2
```

After execution:
- MLflow runs are available in `mlruns/`
- Versioned models are available in `model_registry/`
- Latest versions are in `model_registry/<model_name>/latest/model.pkl`

## 3) Launch MLflow UI

```bash
mlflow ui --backend-store-uri ./mlruns --port 5001
```

Open: `http://localhost:5001`

## 4) Start API + Web app (local)

Terminal 1:
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8010
```

Terminal 2:
```bash
python app.py
```

Open:
- Web page placeholder: `http://localhost:5050`
- API docs: `http://localhost:8010/docs`

If one URL appears blank in your browser, prefer the loopback form:
- MLflow: `http://127.0.0.1:5001`
- API docs: `http://127.0.0.1:8010/docs`
- Web app: `http://127.0.0.1:5050`

## 5) Test prediction endpoint

Example request:

```bash
curl -X POST http://localhost:8010/predict \
  -H "Content-Type: application/json" \
  -d "{\"model_type\":\"budget\",\"features\":{\"flowtype\":1,\"participants\":30,\"budget_sub_category\":2,\"budget_month\":6,\"duration_days\":3,\"season\":2024}}"
```

## 6) Dockerized run (recommended)

```bash
docker compose up --build
```

Services:
- `trainer`: runs automated pipeline and creates at least 2 tracked runs
- `api`: FastAPI prediction service on `http://localhost:8000`
- `web`: Flask web app on `http://localhost:5050`

## 7) Minimal automated test

```bash
pytest -q
```

## Validation checklist mapping (S12)

- Experiment Tracking (MLflow): yes (`mlops/training_pipeline.py`, `mlruns/`)
- Automated Pipeline: yes (`python -m mlops.training_pipeline --runs 2`)
- Model Management/versioning: yes (`model_registry/<model>/timestamp_runid`)
- Model Serving API: yes (`api/main.py`, `/predict`)
- Containerization: yes (`Dockerfile.api`, `Dockerfile.web`, `docker-compose.yml`)
- Code quality + tests: basic structure + `tests/test_api.py`
- Web app integration: minimal verification page (`index.html` calls FastAPI `/predict`)
