# Monitoring (Week S13) — Prometheus & Grafana

## What was implemented

- **`/metrics`** on the FastAPI app (`prometheus_client`) — traffic, latency histogram, errors, validation errors, model health vs baseline, classifier confidence, drift flags, freshness timestamps.
- **Logs** — `logs/scout_api.log` (warnings for high latency, drift simulation, validation errors).
- **Prometheus** — scrape every **15s** (`monitoring/prometheus.yml`). Targets the API at `host.docker.internal:8010` (Docker Desktop).
- **Alert rules** — `monitoring/alerts.yml` (latency, HTTP errors, validation spike, drift, health ratio).
- **Grafana** — provisioned datasource + dashboard **“Scout MLOps — Overview”** (traffic, latency, errors, confidence, baseline, data quality, drift).
- **Simulations** — `scripts/simulate_monitoring.py` (`traffic`, `errors`, `drift`, `mixed`, `stress`, `all`) ; `pulse_metrics.py` (`--heavy` pour plus de densité).

## Sans Docker (Windows) — Prometheus + Grafana en binaire

1. **Téléchargements officiels**
   - Prometheus : [https://prometheus.io/download/](https://prometheus.io/download/) → archive **windows-amd64** `.zip`
   - Grafana OSS : [https://grafana.com/grafana/download?platform=windows](https://grafana.com/grafana/download?platform=windows) → **Zip** ou MSI  
   - (Option) `winget install Prometheus.Prometheus` / `winget install GrafanaLabs.Grafana.OSS` si `winget` fonctionne chez toi.

2. **API** (racine du dépôt) :  
   `python -m uvicorn api.main:app --host 127.0.0.1 --port 8010`

3. **Prometheus** (adapter le chemin vers `prometheus.exe`) :  
   `prometheus.exe --config.file=monitoring/prometheus.host.yml --web.listen-address=127.0.0.1:9090 --storage.tsdb.path=tools/prometheus-data`  
   Vérifier : [http://127.0.0.1:9090/targets](http://127.0.0.1:9090/targets) → cible **UP**.

4. **Grafana** — variables puis lancer `grafana-server.exe` depuis le dossier Grafana :

   - `GF_PATHS_PROVISIONING` = chemin absolu vers `monitoring/grafana/provisioning.local`
   - `GF_SERVER_HTTP_ADDR` = `127.0.0.1`  
   La datasource Prometheus (`http://127.0.0.1:9090`) est chargée depuis `provisioning.local/datasources/`.

5. **Dashboard** — le provisioning « fichier » des dashboards est capricieux sous Windows ; importe le JSON une fois :  
   `python scripts/import_grafana_dashboard.py`  
   Puis ouvre l’URL affichée (ex. [http://127.0.0.1:3000/d/scout-mlops-overview/...](http://127.0.0.1:3000/)).

6. **Charge de démo** : `python scripts/simulate_monitoring.py traffic`  
   Si Grafana affiche **No data** : lance `python scripts/pulse_metrics.py` (quelques requêtes toutes les 3 s) pendant 1–2 minutes, puis **réimporte** le dashboard après mise à jour du JSON : `python scripts/import_grafana_dashboard.py`.  
   Vérifie aussi l’intervalle de temps Grafana (**Last 1 hour** ou plus).

## Troubleshooting

| Symptom | What to do |
|--------|-------------|
| **`ERR_CONNECTION_REFUSED`** on `:3000` / `:9090` | Monitoring stack is not running. From repo root: `docker compose -f docker-compose.monitoring.yml up -d`. |
| **`404` on `/metrics`** | Restart the API from the **project root**: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8010`. Ensure only one process uses port 8010. |
| Prometheus **Empty targets / down** | API must be up **before** Prometheus; on Windows use Docker Desktop so `host.docker.internal` resolves. |

## Run locally

1. Install deps: `pip install -r requirements.txt`
2. Start API (bind all interfaces so Docker can scrape):

   `python -m uvicorn api.main:app --host 0.0.0.0 --port 8010`

3. Start stack:

   `docker compose -f docker-compose.monitoring.yml up -d`

4. Open **Grafana** http://localhost:3000 — login `admin` / `admin` — dashboard *Scout MLOps — Overview*.  
   **Prometheus** http://localhost:9090 — **Graph** / **Alerts**.

5. Generate load:

   `python scripts/simulate_monitoring.py traffic`

## Week S13 — checklist (énoncé cours)

| Attendu | Où c’est couvert |
|--------|------------------|
| `/metrics` + scrape 10–15 s | `api/main.py`, `monitoring/prometheus.yml` (15s) |
| Dashboard : trafic, latence, erreurs, santé modèle & données | `monitoring/grafana/dashboards/scout-mlops-overview.json` |
| Dérive / dégradation (seuils) | `scout_drift_detected`, ratio santé sous 0,95 (~5 %), confiance, `X-Simulate-Drift` |
| Alertes (latence, erreurs, précision, dérive) | `monitoring/alerts.yml` + logs API |
| Scénarios : trafic, erreurs, dérive | `python scripts/simulate_monitoring.py all` |
| Logs : erreurs, anomalies, retraining | `logs/scout_api.log` (`VALIDATION_ERROR`, `HIGH_LATENCY`, `DRIFT_WARNING`, `RETRAINING_TRIGGER`, …) |
| Baseline | `init_baselines()` dans `api/prometheus_metrics.py` |

**Notifications :** Prometheus alerte dans l’UI ; pour e-mail/Slack il faudrait **Alertmanager** (hors scope minimal du repo). Les **logs** et **Grafana** couvrent la traçabilité côté démo.

## Deliverables for the assignment

- Export dashboard: Grafana → Dashboard → Share → Export → Save JSON (you already have `monitoring/grafana/dashboards/scout-mlops-overview.json`).
- Screenshots: Grafana panels + Prometheus Alerts after running simulations.
- Describe scenarios: high traffic (latency), errors (validation), drift header (degraded confidence).

## Baseline & drift (simple rules)

- Static baselines in metrics (`scout_baseline_accuracy_proxy`, classifier uniform baseline).
- Drift: header **`X-Simulate-Drift: 1`** on `/predict` lowers effective confidence / health for demos; classifier low max-probability triggers log `DRIFT_WARNING`.

## Observability mapping

- **Metrics** — what happens (rates, latency, gauges).
- **Logs** — why / investigate (`logs/scout_api.log`, `ANOMALY_SIMULATION`, `DRIFT_WARNING`, `HIGH_LATENCY`, `VALIDATION_ERROR`).
