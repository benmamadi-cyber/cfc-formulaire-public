# CFC — Formulaire public d'auto-enregistrement des prospects

Intermédiaire **cloud** à déployer sur le VPS public (« CAFCA »), séparé de
l'application interne CFC. Il collecte l'**étape 1** du parcours prospect
(enregistrement de l'intérêt) et met les soumissions à disposition de l'app
interne, qui va les **capter** (pull) via un jeton — sur le modèle de la
passerelle NEXAH.

```
[Prospect] → Formulaire public (ce projet, sur Internet)
                 │ POST /api/soumission
                 ▼
             BDD cloud (soumissions.db)
                 ▲  pull toutes les X min (Bearer token)
             App interne CFC  → prospects_staging → module Affectation
```

## Contenu
| Fichier | Rôle |
|---|---|
| `app_public.py` | API Flask : formulaire + soumission + endpoints de pull |
| `db_public.py` | Base SQLite (`soumissions`) |
| `referentiels.py` | Villes/régions, opérations… (copie autonome de l'app interne) |
| `templates/formulaire.html` | Formulaire public (étape 1) |
| `static/` | CSS + JS (régions↔villes, blocs conditionnels, envoi AJAX) |

## Endpoints
| Méthode | URL | Accès | Rôle |
|---|---|---|---|
| GET | `/` | public | Affiche le formulaire |
| POST | `/api/soumission` | public (rate-limité) | Enregistre une soumission |
| GET | `/api/soumissions?since=<id>` | **Bearer** | Liste les soumissions `nouveau` |
| POST | `/api/soumissions/<id>/consomme` | **Bearer** | Marque une soumission importée |
| GET | `/api/sante` | public | Test de disponibilité |

## Lancer en local
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export SYNC_TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
python app_public.py          # http://localhost:8080
```

## Déploiement sur le VPS (CAFCA)
1. Copier le projet, créer le venv, `pip install -r requirements.txt`.
2. Créer `.env` à partir de `.env.example` et définir un `SYNC_TOKEN` robuste
   (la **même** valeur ira côté app interne dans `CAPTURE_TOKEN`).
3. Servir derrière **gunicorn + reverse proxy TLS** (HTTPS obligatoire) :
   ```bash
   gunicorn -w 2 -b 127.0.0.1:8080 app_public:app
   ```
   puis Nginx/Caddy en frontal pour le certificat Let's Encrypt.
4. Vérifier que seul le proxy expose le port ; garder `Flask-Limiter` actif.

## Sécurité
- Les endpoints de pull renvoient **503** si `SYNC_TOKEN` n'est pas défini,
  **401** si le jeton est absent/incorrect.
- POST public : limité par IP (`RATE_SOUMISSION`, défaut 5/h) + honeypot anti-bot.
- Aucune donnée bancaire sensible n'est obligatoire (revenus/épargne facultatifs).
- Le routage vers l'agence est **recalculé côté interne** à l'import.

> ⚠️ Si les listes (villes, opérations) évoluent dans `cfc-app/constants.py`,
> resynchroniser `referentiels.py`.
