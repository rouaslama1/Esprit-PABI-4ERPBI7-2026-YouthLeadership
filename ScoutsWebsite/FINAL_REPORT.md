# Rapport final — Scouts Vision Studio

## 1. Idee generale

Scouts Vision Studio est une application web pour aider les responsables scouts a suivre le groupe, consulter les chiffres importants et obtenir des previsions simples.

L'application contient :

- un espace utilisateur avec connexion ;
- des tableaux selon le role de l'utilisateur ;
- des previsions pour les membres, les publications, le budget et l'unite ;
- un assistant appele ScoutBot ;
- un suivi technique pour verifier que les services fonctionnent bien.

Les textes visibles dans l'application ont ete simplifiés pour eviter les mots trop techniques. Par exemple, `Dashboard` devient `Tableaux`, `Predictions` devient `Previsions`, `Status` devient `Etat`, et `Objective` devient `But`.

## 2. Roles des utilisateurs

- Group Leader : voit les previsions des membres, publications, unite et budget. Il peut aussi utiliser `Upload Data` et `Reset Data` dans la prevision des membres.
- Finance Manager : voit surtout la prevision du budget.
- Unit Leader : voit les previsions des membres, publications et unite, sans budget.

## 3. Outils utilises

| Outil | Commande | Explication simple |
|---|---|---|
| Node.js / npm | `npm install` | Installe les bibliotheques de l'application web. |
| Vite / React | `npm run dev` | Lance l'application web en local. |
| Build web | `npm run build` | Prepare une version finale de l'application. |
| Verification du code web | `npm run lint` | Verifie les erreurs de code et de style. |
| API de prevision | `npm run ml-api` | Lance le service qui calcule les previsions. |
| Entrainement Machine Learning | `npm run ml-train` | Recalcule certains modeles avec les donnees d'entrainement. |
| MLflow | `npm run mlflow-ui` | Ouvre l'outil qui garde l'historique des essais de modeles. |
| Prometheus | `npm run prometheus` | Recupere les informations de sante du service de prevision. |
| Grafana | `npm run grafana` | Affiche ces informations sous forme de tableaux visuels. |
| Docker | `docker compose up --build` | Lance plusieurs services ensemble : prevision, MLflow, Prometheus et Grafana. |
| Python | `python -m py_compile ml_backend/predict_service.py ml_backend/main.py` | Verifie que les fichiers Python modifies ne contiennent pas d'erreurs de syntaxe. |

## 4. Machine Learning

Le Machine Learning est la partie qui permet a l'application de calculer des previsions a partir de donnees.

Dans ce projet, il sert a :

- prevoir le nombre de membres ;
- estimer le budget d'une activite ;
- aider a suivre l'etat d'une unite ;
- analyser les reactions des publications.

Les fichiers des modeles sont places a la racine de `scouts-vision-studio`, par exemple :

- `arima_model.pkl` pour la prevision des membres ;
- `budget_rf.pkl` pour le budget ;
- `classification_lr.pkl` pour l'etat de l'unite ;
- `kmeans_model.pkl` pour les publications.

Le code principal des previsions se trouve dans :

- `scouts-vision-studio/ml_backend/main.py`
- `scouts-vision-studio/ml_backend/predict_service.py`

## 5. MLOps

MLOps signifie organisation et suivi des modeles de Machine Learning.

Dans ce projet, MLOps permet de garder une trace :

- des entrainements des modeles ;
- des resultats obtenus ;
- des fichiers generes ;
- des versions des modeles.

Commande :

```bash
npm run mlflow-ui
```

Lien local :

```text
http://127.0.0.1:5001
```

Emplacement des historiques :

```text
scouts-vision-studio/mlops/mlruns/
```

Console interne :

```text
/ops/mlflow
```

Cette console est prevue pour l'equipe technique, pas pour l'utilisateur final.

## 6. Prometheus

Prometheus sert a surveiller le service de prevision.

Il recupere regulierement des informations comme :

- nombre de demandes ;
- erreurs ;
- temps de reponse ;
- etat general du service.

Commande :

```bash
npm run prometheus
```

Lien local :

```text
http://127.0.0.1:9090
```

Fichiers importants :

```text
scouts-vision-studio/monitoring/prometheus.native.yml
scouts-vision-studio/monitoring/prometheus.yml
scouts-vision-studio/monitoring/alerts.yml
```

## 7. Grafana

Grafana sert a afficher les informations de Prometheus avec des graphiques.

Commande :

```bash
npm run grafana
```

Lien local :

```text
http://127.0.0.1:3000
```

Identifiants habituels en local :

```text
admin / admin
```

Emplacement du tableau Grafana :

```text
scouts-vision-studio/monitoring/grafana/dashboards/scouts-s13.json
```

## 8. Ajout des donnees pour le Group Leader

Une fonction speciale a ete ajoutee uniquement pour le `Group Leader` dans la prevision des membres.

Boutons ajoutes :

- `Upload Data` : ajoute des donnees supplementaires a la prevision des membres.
- `Reset Data` : retire ces donnees et remet la prevision initiale.

Important : cette fonction touche seulement la prevision des membres. Elle ne change pas le budget, les publications ou l'unite.

Emplacement du document de donnees ajoutees :

```text
scouts-vision-studio/public/data/group-leader-forecast-upload.json
```

Contenu du fichier :

```json
{
  "name": "Donnees ajoutees pour la prevision des membres",
  "description": "Donnees utilisees uniquement par le bouton Upload Data du Group Leader.",
  "rows": [
    {
      "season": "2026-2027",
      "members": 118
    },
    {
      "season": "2027-2028",
      "members": 132
    }
  ]
}
```

Fichiers modifies pour cette fonction :

- `scouts-vision-studio/src/routes/workspace.predictions.tsx`
- `scouts-vision-studio/ml_backend/predict_service.py`
- `scouts-vision-studio/ml_backend/main.py`

## 9. Lancement conseille

Depuis le dossier :

```bash
cd scouts-vision-studio
```

Lancer l'application :

```bash
npm run dev
```

Lancer le service de prevision :

```bash
npm run ml-api
```

Lancer le suivi technique :

```bash
npm run prometheus
npm run grafana
```

Lancer l'historique des modeles :

```bash
npm run mlflow-ui
```

## 10. Verification finale

Commandes utilisees pour verifier le projet :

```bash
npm run lint
npm run build
python -m py_compile ml_backend/predict_service.py ml_backend/main.py
```

Resultat : les verifications passent.

## 11. Emplacements principaux

- Interface web : `scouts-vision-studio/src/`
- Pages utilisateur : `scouts-vision-studio/src/routes/`
- Menu lateral : `scouts-vision-studio/src/components/dashboard/WorkspaceShell.tsx`
- Service de prevision : `scouts-vision-studio/ml_backend/`
- Donnees ajoutees au forecast : `scouts-vision-studio/public/data/group-leader-forecast-upload.json`
- Suivi Prometheus / Grafana : `scouts-vision-studio/monitoring/`
- Historique des modeles : `scouts-vision-studio/mlops/`

Fin du rapport.
