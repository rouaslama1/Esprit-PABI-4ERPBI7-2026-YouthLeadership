# Rapport technique — validation semaine 13 (monitoring MLOps)

**À lire en parallèle :** commandes ordonnées + URLs + requêtes Prometheus → `[COMMANDES_ET_LIENS_S13.txt](COMMANDES_ET_LIENS_S13.txt)`

**Projet :** Scout Dashboard  
**Objectif global :** Chaîne **production-like** — métriques Prometheus, dashboards Grafana, alertes, logs, scénarios de charge, comparaison à une baseline.

---

## 1. Outils et rôle (court)


| Outil                                                | Rôle                                                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **prometheus-client** (Python)                       | Expose `GET /metrics` et enregistre compteurs / histogrammes / gauges.                     |
| **FastAPI**                                          | API métier + middleware HTTP + instrumentation `/predict`.                                 |
| **Prometheus**                                       | Scrape `/metrics`, stocke TSDB, évalue `alerts.yml`.                                       |
| **Grafana**                                          | Visualise les métriques (dashboard JSON + datasource).                                     |
| **Docker Compose** (`docker-compose.monitoring.yml`) | *Optionnel* — lance Prometheus + Grafana ; sans Docker → binaires + `prometheus.host.yml`. |
| **httpx**                                            | Scripts de simulation (`simulate_monitoring`, `pulse_metrics`).                            |
| **Logging stdlib**                                   | Fichier `logs/scout_api.log` (anomalies, drift, latence).                                  |
| **Flask** (existant S12)                             | UI `index.html`, routes `/mlflow`, proxy API.                                              |
| **MLflow UI** (CLI)                                  | Consultation des runs (hors processus Grafana).                                            |


---

## 2. Fichiers ajoutés ou modifiés (S13)


| Fichier / dossier                                         | Modification                                                                            | Objectif                                                                   |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `api/main.py`                                             | Middleware + appels `pm.`* + `GET /metrics` + logs                                      | Mesurer trafic, latence, erreurs ; exposer Prometheus ; tracer événements. |
| `api/prometheus_metrics.py`                               | Métriques `scout_`*, baselines, drift, lenteurs HTTP                                    | « Quoi » mesurer pour trafic, santé modèle, données, dérive.               |
| `api/logging_conf.py`                                     | (existant / utilisé)                                                                    | Centraliser logs fichier + console.                                        |
| `monitoring/prometheus.yml`                               | Scrape 15 s, cible Docker `host.docker.internal:8010`                                   | Collecte quand l’API tourne sur l’hôte.                                    |
| `monitoring/prometheus.host.yml`                          | Scrape `127.0.0.1:8010`                                                                 | Même chose **sans Docker** (Prometheus binaire Windows).                   |
| `monitoring/alerts.yml`                                   | Règles latence, erreurs, validation, drift, santé                                       | Alerting « simple » côté Prometheus.                                       |
| `monitoring/grafana/provisioning/`                        | Datasource + provider (stack Docker)                                                    | Grafana auto-config en conteneur.                                          |
| `monitoring/grafana/provisioning.local/`                  | Datasource `127.0.0.1:9090`                                                             | Grafana **natif** Windows.                                                 |
| `monitoring/grafana/dashboards/scout-mlops-overview.json` | Panneaux trafic, latence, erreurs, santé, données, drift                                | Storytelling observabilité.                                                |
| `docker-compose.monitoring.yml`                           | Services `prometheus` + `grafana`                                                       | Démarrage stack monitoring.                                                |
| `scripts/simulate_monitoring.py`                          | `traffic`, `errors`, `drift`, `mixed`, `stress`, `all` ; options `--workers`, `--total` | Charge ponctuelle, erreurs, dérive, mix modèles, grosse démo.              |
| `scripts/pulse_metrics.py`                                | Boucle `/predict` ; `--heavy` = rafales plus denses                                     | Séries continues visibles dans Prometheus/Grafana.                         |
| `scripts/import_grafana_dashboard.py`                     | POST JSON vers API Grafana                                                              | Import dashboard fiable (provisioning fichier capricieux sous Windows).    |
| `tests/test_api.py`                                       | Test `/metrics`                                                                         | Non-régression.                                                            |
| `requirements.txt`                                        | `prometheus-client`, `httpx`                                                            | Dépendances monitoring.                                                    |
| `monitoring/README.md`                                    | Procédures Docker + natif + troubleshooting                                             | Mode d’emploi.                                                             |
| `.gitignore`                                              | `logs/`, `tools/`                                                                       | Ne pas versionner logs ni binaires locaux.                                 |


---

## 3. Relations (flux)

```
Navigateur / scripts ──HTTP──► FastAPI :8010 (/predict, /metrics, /health, /docs)
                                    │
Prometheus (:9090) ◄── scrape 15s ──┘
       │
       └── datasource ──► Grafana :3000 (dashboard scout-mlops-overview.json)

Logs : api → logs/scout_api.log
Alertes : prometheus charge monitoring/alerts.yml
```

**Sans Docker :** Prometheus et Grafana sont lancés en binaire ; config scrape = `prometheus.host.yml` ; Grafana import dashboard via `import_grafana_dashboard.py`.

---

## 4. Comment chaque outil est utilisé (très bref)

- **prometheus-client** : import dans `api/main.py` / `prometheus_metrics.py` ; `generate_latest()` pour `/metrics`.
- **Prometheus** : lit `prometheus.yml` (+ `alerts.yml`) ; UI sur `:9090` (Graph, Targets, Alerts).
- **Grafana** : datasource pointant vers Prometheus ; dashboard importé ou provisionné ; explore les séries `scout_`*.
- **Docker** : `docker compose -f docker-compose.monitoring.yml up -d` lance Prometheus + Grafana pré-configurés.
- **Scripts Python** : `simulate_monitoring` = pics (`stress` / `mixed` pour beaucoup de points) ; `pulse_metrics` = flux continu (`--heavy` pour densifier).
- **Logs** : warnings / erreurs métier écrits via `log` dans `api/main.py` lors de drift simulé, latence, validation.

---

## 5. Livrables S13 couverts

Métriques `/metrics`, scrape 10–15 s, dashboard interprétable, règles drift/dégradation simples, alertes, scénarios simulés, logs + baseline, comparaison dans Grafana/Prometheus.

---

## 6. Fiche de révision (ordre logique)

1. **Démarrer l’API** sur `8010` → sans ça, `/metrics` vide ou cible Prometheus **DOWN**.
2. **Prometheus** scrape `127.0.0.1:8010/metrics` (fichier `monitoring/prometheus.host.yml` si pas Docker).
3. **Vérifier** `http://127.0.0.1:9090/targets` → job **UP**.
4. **Générer du trafic** : `pulse_metrics.py` (continu) ou `simulate_monitoring.py stress` / `mixed` (pic riche).
5. **Prometheus Graph** : au minimum `scout_predictions_total`, `scout_http_requests_total`, `rate(...[1m])`.
6. **Grafana** (optionnel) : datasource Prometheus, dashboard importé ; mêmes séries `scout_`*.
7. **Alertes** : `monitoring/alerts.yml` chargée par Prometheus ; onglet **Alerts**.
8. **Logs** : `logs/scout_api.log` pour corréler drift / lenteurs avec les pics de métriques.

**À savoir par cœur pour l’oral / le rapport :** le flux *client → FastAPI → `/metrics` ← scrape Prometheus → Grafana* ; la différence *compteur* (toujours croissant) vs *gauge* ; pourquoi on utilise `rate()` sur les compteurs.

---

## 7. Conformité au brief S13 (réviser avec ce tableau)

Texte de référence : consigne « production-like monitoring » (Prometheus, Grafana, drift, alertes, simulations, observabilité, baseline). Ci-dessous : **exigence → statut → où c’est dans le projet**.

### 7.1 Prometheus


| Exigence                 | Statut | Preuve dans le dépôt                                                                        |
| ------------------------ | ------ | ------------------------------------------------------------------------------------------- |
| Métriques via `/metrics` | OK     | `api/main.py` (`generate_latest`, route `/metrics`)                                         |
| Scrape 10–15 s           | OK     | `scrape_interval: 15s` dans `monitoring/prometheus.host.yml` et `monitoring/prometheus.yml` |
| Activité en temps réel   | OK     | `api/prometheus_metrics.py` + middleware `api/main.py`                                      |


### 7.2 Grafana


| Exigence                                       | Statut             | Preuve                                                                                                                                                                               |
| ---------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Trafic (évolution requêtes)                    | OK                 | `scout-mlops-overview.json` : prédictions/s, HTTP par route, compteur brut                                                                                                           |
| Performance (latence)                          | OK                 | Histogramme `scout_prediction_latency_seconds` (p50/p95), taux `/predict` lents                                                                                                      |
| Stabilité (taux d’erreur)                      | OK                 | `scout_http_errors_total`                                                                                                                                                            |
| Santé modèle (accuracy vs baseline, confiance) | Partiel (proxy)    | `scout_model_health_vs_baseline_ratio`, `scout_classifier_max_confidence_ratio`, baselines dans `init_baselines()` — pas d’accuracy en ligne réelle, mais règles « production-like » |
| Santé données (manquants, fraîcheur)           | OK                 | `scout_data_validation_errors_total`, `scout_feature_completeness_ratio`, `scout_last_success_unix_timestamp`                                                                        |
| Dashboard lisible (storytelling)               | OK                 | Titres des panneaux dans le JSON Grafana                                                                                                                                             |
| Captures / export                              | À fournir au rendu | JSON déjà versionné ; ajouter screenshots pendant `stress` ou `all`                                                                                                                  |


### 7.3 Dérive et dégradation


| Exigence                        | Statut | Preuve                                                                                             |
| ------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| Shift de distribution (données) | Proxy  | Pas de PSI/KL ; pics validation + flags `scout_drift_detected` ; règles simples conformes au brief |
| Baisse accuracy > 5 %           | Proxy  | Alerte `ModelHealthBelowBaseline` si ratio `< 0.95` (`monitoring/alerts.yml`)                      |
| Baisse de confiance             | OK     | `ClassifierDriftSignal`, log `DRIFT_WARNING` dans `api/main.py`                                    |
| Règles / seuils simples         | OK     | Python (`record_success`, en-tête `X-Simulate-Drift`) + PromQL dans `alerts.yml`                   |


### 7.4 Alerting


| Exigence                 | Statut                       | Preuve                                                                                                                           |
| ------------------------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Haute latence            | OK                           | `HighPredictionLatencyP90`, `LatencyDegradationPath`                                                                             |
| Taux d’erreur élevé      | OK                           | `ElevatedHTTPErrors`, `ValidationErrorsSpike`                                                                                    |
| Dégradation accuracy     | OK                           | `ModelHealthBelowBaseline`                                                                                                       |
| Drift                    | OK                           | `ClassifierDriftSignal`, `DriftAccuracyProxy`                                                                                    |
| Logs et/ou notifications | Logs OK ; pas d’e-mail/Slack | `logs/scout_api.log` ; UI **Alerts** Prometheus ; Alertmanager non branché (mentionner à l’oral si on demande « notifications ») |


### 7.5 Simulations (obligatoires)


| Scénario                         | Statut | Commande / fichier                                                             |
| -------------------------------- | ------ | ------------------------------------------------------------------------------ |
| Fort trafic → impact latence     | OK     | `scripts/simulate_monitoring.py` : `traffic`, `stress`, `--workers`, `--total` |
| Erreurs API → pics               | OK     | `errors`                                                                       |
| Drift modèle                     | OK     | `drift` (en-tête `X-Simulate-Drift`)                                           |
| Monitoring reflète les scénarios | OK     | Métriques + alertes + logs après exécution                                     |


### 7.6 Observabilité


| Exigence                           | Statut               | Preuve                                                   |
| ---------------------------------- | -------------------- | -------------------------------------------------------- |
| Logs : erreurs, anomalies          | OK                   | `api/logging_conf.py`, messages dans `api/main.py`       |
| Déclencheurs retraining            | OK                   | `RETRAINING_TRIGGER` si drift simulé                     |
| Métriques = quoi / logs = pourquoi | À expliquer à l’oral | Agrégation Prometheus vs événements dans `scout_api.log` |


### 7.7 Baseline


| Exigence             | Statut | Preuve                                                                                                         |
| -------------------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| Valeurs de référence | OK     | `BASELINE_ACCURACY_PROXY`, `CLASSIFIER_CONFIDENCE_BASELINE`, `MODEL_HEALTH_RATIO` dans `prometheus_metrics.py` |
| Écarts détectables   | OK     | Gauges + alertes + dashboard Grafana                                                                           |


### 7.8 Phrases utiles pour l’oral (révision rapide)

- **Architecture :** client → FastAPI → exposition `/metrics` → scrape Prometheus (15 s) → Grafana ; règles dans `monitoring/alerts.yml`.
- **Limites assumées :** drift et accuracy sont **proxy / simulés** ; pas d’Alertmanager ; distribution shift statistique non implémenté (hors scope « règles simples »).
- **Démonstration :** lancer API + Prometheus, `simulate_monitoring.py stress`, montrer **Targets UP**, **Graph**, **Alerts**, et une ligne de log `HIGH_LATENCY` ou `DRIFT_WARNING`.

---

*Commandes pas à pas : `docs/COMMANDES_ET_LIENS_S13.txt`.*