================================================================================
  Scouts Website — commandes pour lancer l’application, l’API ML et MLflow
================================================================================

  Rapport final synthétique (outils, liens, MLflow, Prometheus/Grafana) :
    FINAL_REPORT.md  (à la racine du dépôt ScoutsWebsite)

================================================================================

Tout se fait depuis le dossier du projet front + API :

  cd scouts-vision-studio


--------------------------------------------------------------------------------
  Prérequis
--------------------------------------------------------------------------------

  • Node.js (npm) — pour l’application web
  • Python 3.11+ — pour l’API FastAPI, MLflow et le pipeline


--------------------------------------------------------------------------------
  Installation (une fois)
--------------------------------------------------------------------------------

  npm install

  pip install -r ml_backend/requirements.txt


--------------------------------------------------------------------------------
  Lancer l’application web (interface utilisateur)
--------------------------------------------------------------------------------

  npm run dev

  Ouvrir dans le navigateur l’URL indiquée dans le terminal (souvent une des suivantes) :

    http://localhost:8080/
    http://localhost:8081/

  (Le port peut varier si 8080 est déjà utilisé.)


--------------------------------------------------------------------------------
  Lancer l’API ML (FastAPI)
--------------------------------------------------------------------------------

  Dans un second terminal, toujours dans scouts-vision-studio :

  npm run ml-api

  • API :           http://127.0.0.1:5050/
  • Swagger UI :    http://127.0.0.1:5050/docs
  • ReDoc :         http://127.0.0.1:5050/redoc
  • Santé :         http://127.0.0.1:5050/health
  • Prédictions :   POST http://127.0.0.1:5050/predict

  L’app web appelle l’API via le proxy Vite (/api/ml → port 5050). Pour que les
  prédictions fonctionnent, l’API doit être démarrée en parallèle de npm run dev.


--------------------------------------------------------------------------------
  Lancer l’interface MLflow (suivi des expériences — équipe technique)
--------------------------------------------------------------------------------

  Dans un troisième terminal, toujours dans scouts-vision-studio :

  npm run mlflow-ui

  Lien MLflow UI :

    http://127.0.0.1:5001

  (Magasin local des runs : scouts-vision-studio/mlops/mlruns/)


--------------------------------------------------------------------------------
  Console web technique (runs + registry, sans lien dans le menu)
--------------------------------------------------------------------------------

  Une fois connecté et avec npm run dev actif, ouvrir (adapter le port du dev) :

    http://localhost:8080/ops/mlflow
    http://localhost:8081/ops/mlflow

  Remplacer le port par celui affiché au démarrage de « npm run dev ».


--------------------------------------------------------------------------------
  Pipeline d’entraînement MLOps (optionnel)
--------------------------------------------------------------------------------

  Depuis scouts-vision-studio :

  npm run ml-train

  !!!!!(équivalent : npm run ml-pipeline  ou  python -m ml_backend.pipeline.train_pipeline)


--------------------------------------------------------------------------------
  Prometheus en local — pourquoi localhost:9090 refuse la connexion ?
--------------------------------------------------------------------------------

  L’API ML expose les métriques sur le port 5050 (/metrics). Prometheus est un
  **autre programme** : tant qu’il n’est pas lancé, **rien n’écoute le port 9090**,
  d’où « ERR_CONNECTION_REFUSED » dans le navigateur.

  Ordre recommandé :
    1) Démarrer l’API :  cd scouts-vision-studio  puis  npm run ml-api
       Vérifier : http://127.0.0.1:5050/metrics
    2) Démarrer Prometheus (SANS Docker : section suivante ; avec Docker : plus bas).
    3) Ouvrir l’interface Prometheus : http://127.0.0.1:9090  (ou http://localhost:9090)

  Dans Prometheus : menu « Status → Targets » : l’état doit être UP.
  Onglet « Graph » : essayer par exemple  rate(scout_predict_requests_total[1m])


--------------------------------------------------------------------------------
  Prometheus DÉJÀ installé — une commande pour l’activer
--------------------------------------------------------------------------------

  Si « Get-Command prometheus » ne renvoie rien, Prometheus n’est pas dans le PATH.
  Téléchargement automatique (Windows, une fois) :

    cd scouts-vision-studio
    npm run prometheus:download-win

  Cela place prometheus.exe dans monitoring\ . Ensuite :

    npm run prometheus

  Depuis le dossier scouts-vision-studio (l’API doit tourner : npm run ml-api) :

    npm run prometheus

  Le script cherche l’exécutable dans cet ordre :
    1) variable SCOUT_PROMETHEUS_EXE (ou PROMETHEUS_EXE) = chemin complet vers prometheus.exe
    2) fichier scouts-vision-studio\monitoring\prometheus.exe (copie locale)
    3) prometheus.exe / prometheus dans le PATH

  Si « non reconnu » : PowerShell, une seule session :

    $env:SCOUT_PROMETHEUS_EXE="C:\chemin\vers\votre\prometheus.exe"
    npm run prometheus

  Ou à la main (toujours depuis scouts-vision-studio) :

    prometheus --config.file=monitoring/prometheus.native.yml --web.listen-address=127.0.0.1:9090

  Visualiser l’interface : ouvrir le navigateur sur

    http://127.0.0.1:9090

  (ou http://localhost:9090 — même chose.)

  Sous Windows sans npm : double-clic sur
    scouts-vision-studio\monitoring\start-prometheus-windows.cmd
  (utilise Prometheus dans le PATH ou prometheus.exe dans ce dossier.)


--------------------------------------------------------------------------------
  Grafana en local (sans Docker) — télécharger, lancer, ouvrir l’interface
--------------------------------------------------------------------------------

  Grafana n’est pas le même programme que Prometheus : il faut aussi l’installer
  localement (ou utiliser Docker Compose). Sans Docker, le projet fournit :

    • Téléchargement (Windows, une fois) :
        cd scouts-vision-studio
        npm run grafana:download-win

      Cela extrait Grafana OSS dans monitoring\grafana-win\

    • Lancer Grafana (après Prometheus sur le port 9090) :
        npm run grafana

    • Interface web :
        http://127.0.0.1:3000

      Connexion par défaut : admin / admin

  Ouvrir le bon écran : menu **Dashboards** → **Browse** → dossier **S13 MLOps** →
  **Scouts Vision**. (La page **Snapshots** est vide si tu n’as rien
  exporté — ce n’est pas le tableau de bord temps réel.)

  La datasource Prometheus pointe vers http://127.0.0.1:9090 (stack « native »).
  Les tableaux de bord S13 sont chargés depuis monitoring/grafana/dashboards/ .

  Ordre des 3 terminaux :
    1) npm run ml-api
    2) npm run prometheus
    3) npm run grafana

  Dossier de données Grafana (local, ignoré par Git) : monitoring/grafana-data/

  Si Grafana refuse de démarrer (erreur SQLite « cannot find the path ») :
    mettre à jour le dépôt et relancer  npm run grafana  — le script crée
    automatiquement monitoring/grafana-data/ et les logs.

  Chaîne complète pour des graphes à jour après chaque prédiction :
    • API expose /metrics ; Prometheus scrape toutes les 15 s (prometheus.native.yml) ;
    • Grafana interroge Prometheus (datasource 127.0.0.1:9090) ; le tableau S13
      se rafraîchit toutes les 5 s. Après un clic « Generate forecast » dans l’app,
      attendre au plus ~15–20 s pour voir les compteurs augmenter.


--------------------------------------------------------------------------------
  SANS DOCKER — Installer Prometheus sur Windows et ouvrir l’interface
--------------------------------------------------------------------------------

  Tu n’as pas besoin de Docker. Prometheus est un exécutable à télécharger.

  Étape 1 — Télécharger Prometheus (Windows)
    • Aller sur : https://github.com/prometheus/prometheus/releases
    • Télécharger l’archive du type : prometheus-*-windows-amd64.zip
    • Décompresser l’archive.

  Étape 2 — Placer prometheus.exe à côté de la config du projet
    Copier le fichier prometheus.exe (et les fichiers .dll du même dossier s’il y en a)
    dans le dossier du projet :

      scouts-vision-studio\monitoring\

    (au même endroit que prometheus.native.yml et alerts.yml)

  Étape 3 — Lancer l’API ML (terminal 1)
      cd scouts-vision-studio
      npm run ml-api

    Vérifier dans le navigateur : http://127.0.0.1:5050/metrics

  Étape 4 — Lancer Prometheus (terminal 2)

    Option A — double-clic ou ligne de commande :

      cd scouts-vision-studio\monitoring
      start-prometheus-windows.cmd

    Option B — commande manuelle :

      cd scouts-vision-studio\monitoring
      prometheus.exe --config.file=prometheus.native.yml --web.listen-address=127.0.0.1:9090

  Étape 5 — Ouvrir l’interface dans le navigateur
      http://127.0.0.1:9090

    • Menu « Status » → « Targets » : la cible 127.0.0.1:5050 doit être « UP ».
    • « Graph » : tester une requête, ex.  up  ou  scout_predict_requests_total

  Linux / macOS (sans Docker) : télécharger le .tar.gz pour ta plate-forme, extraire
  l’exécutable « prometheus », puis dans le dossier monitoring :

      ./prometheus --config.file=prometheus.native.yml --web.listen-address=127.0.0.1:9090


--------------------------------------------------------------------------------
  Méthode A — Prometheus seul avec Docker (API déjà sur l’hôte, port 5050)
--------------------------------------------------------------------------------

  Prérequis : Docker Desktop (ou Docker Engine) installé et démarré.

  Ouvrir un **nouveau terminal**, aller dans le dossier **scouts-vision-studio** :

    cd scouts-vision-studio

  PowerShell :

    docker run --rm -p 9090:9090 `
      -v "${PWD}/monitoring/prometheus.host.yml:/etc/prometheus/prometheus.yml:ro" `
      -v "${PWD}/monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro" `
      prom/prometheus:v2.52.0

  Invite de commandes cmd.exe (chemins relatifs au dossier courant) :

    docker run --rm -p 9090:9090 -v "%CD%\monitoring\prometheus.host.yml:/etc/prometheus/prometheus.yml:ro" -v "%CD%\monitoring\alerts.yml:/etc/prometheus/alerts.yml:ro" prom/prometheus:v2.52.0

  Puis dans le navigateur : http://localhost:9090

  La config prometheus.host.yml scrape host.docker.internal:5050 (l’API sur ta
  machine). Si la cible reste DOWN : sous Linux ajouter au docker run :
    --add-host=host.docker.internal:host-gateway


--------------------------------------------------------------------------------
  Méthode B — Tout avec Docker Compose (API + Prometheus + Grafana + MLflow)
--------------------------------------------------------------------------------

  Depuis scouts-vision-studio :

  docker compose up --build

  • API ML (Swagger) : http://localhost:5050/docs
  • Métriques Prometheus (scraping) : http://localhost:5050/metrics
  • MLflow UI :        http://localhost:5001
  • Prometheus UI :   http://localhost:9090
  • Grafana :          http://localhost:3000  (utilisateur : admin  mot de passe : admin)

  Ouvrir Prometheus : lancer un navigateur sur http://localhost:9090
    — Menu « Status → Targets » : vérifier que la cible scout_ml_api est UP.
    — « Graph » : requêtes du type rate(scout_predict_requests_total[1m])
    — « Alerts » : règles S13 (latence, erreurs, dérive, données).

  Ouvrir Grafana : http://localhost:3000 , se connecter (admin / admin).
    — Aller dans « Dashboards » : dossier « S13 MLOps » → « Scouts Vision ».
    — Les panneaux couvrent trafic, latence, erreurs, santé modèle/données, dérive, retraining.

  (Si tu préfères lancer Docker depuis la racine du dépôt « ScoutsWebsite » au lieu
  de « scouts-vision-studio », remplace les volumes par :
    ${PWD}/scouts-vision-studio/monitoring/prometheus.host.yml  etc.)


--------------------------------------------------------------------------------
  Monitoring S13 (développement local sans Grafana)
--------------------------------------------------------------------------------

  1) Installer les dépendances Python si besoin : pip install -r ml_backend/requirements.txt
  2) Terminal 1 : npm run ml-api   (API sur le port 5050, endpoint /metrics actif)
  3) Terminal 2 : section « SANS DOCKER » (prometheus.native.yml) ou Docker si tu l’utilises

  Variables d’environnement utiles (baselines & alertes logiques) :
    SCOUT_BASELINE_CONFIDENCE_PCT   (défaut 50)
    SCOUT_BASELINE_LATENCY_MS       (défaut 2000)
    SCOUT_BASELINE_ACCURACY_RATIO    (défaut 1.0)
    SCOUT_LOG_LEVEL                  INFO ou DEBUG

  Scénarios de simulation (charge, erreurs, dérive) — API doit tourner :

    npm run monitor:simulate-traffic
    npm run monitor:simulate-errors
    npm run monitor:simulate-drift

  Simulation d’incidents côté serveur (redémarrer l’API après changement) :
    SCOUT_SIM_LATENCY_MS=750        — ralentit chaque /predict (impact latence)
    SCOUT_SIM_CONFIDENCE=1          — incrémente métriques / logs « dérive confiance »
    SCOUT_SIM_ACCURACY=1            — baisse le proxy précision vs baseline (dégradation)

  Les logs structurés (erreurs, anomalies, retraining) vont sur la sortie du processus
  uvicorn (logger « scout.monitoring »). Métriques = ce qui se passe ; logs = pourquoi.


--------------------------------------------------------------------------------
  Arborescence Prometheus / Grafana (fichiers de config dans le projet)
--------------------------------------------------------------------------------

  Voir : scouts-vision-studio/monitoring/README.md
  (liste des répertoires, rôle de chaque YAML/JSON, intervalle de scrape 15 s.)


--------------------------------------------------------------------------------
  Documentation MLOps (critères, livrables)
--------------------------------------------------------------------------------

  Voir le fichier : scouts-vision-studio/MLOPS.md

================================================================================

Terminal 1 : npm run dev

promethieuse : npm run prometheus
http://127.0.0.1:9090


1) npm run ml-api
2) npm run prometheus
3) npm run Grafana
http://127.0.0.1:3000


http://localhost:8081/ops/mlflow



# mouch sure Terminal 2 : npm run qa-api