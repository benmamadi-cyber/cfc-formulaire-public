# Déploiement sur Render (plateforme managée) + domaine personnalisé

Objectif : mettre le formulaire public en ligne sur une URL stable
(ex. `https://crm-cfc-register.com`), avec **PostgreSQL persistant**, sans gérer
de serveur. L'app interne CFC continue de **capter** les données par pull.

```
Client (Internet) → https://crm-cfc-register.com  (Render : Flask + gunicorn)
                              │  écrit dans
                              ▼
                    PostgreSQL managé (Render)
                              ▲  pull HTTPS + token (CAPTURE_TOKEN)
                    App interne CFC → prospects_staging → Affectation
```

---

## Prérequis (comptes à toi)
1. Un compte **GitHub** (pour héberger le code).
2. Un compte **Render** (gratuit) — https://render.com
3. Le **nom de domaine** acheté (ex. `crm-cfc-register.com`).

---

## Étape 1 — Pousser le code sur GitHub
Le dépôt est déjà initialisé et commité en local. Crée un dépôt **vide** sur
GitHub (ex. `cfc-formulaire-public`, privé), puis :

```bash
cd /Users/apple/cfc-formulaire-public
git remote add origin https://github.com/<ton-compte>/cfc-formulaire-public.git
git branch -M main
git push -u origin main
```

## Étape 2 — Déployer sur Render (Blueprint)
1. Sur Render : **New +** → **Blueprint**.
2. Connecte ton GitHub et sélectionne le dépôt `cfc-formulaire-public`.
3. Render lit `render.yaml` et propose de créer :
   - le **service web** `cfc-formulaire` (Flask + gunicorn),
   - la **base PostgreSQL** `cfc-soumissions-db`,
   - et les relie automatiquement (`DATABASE_URL`).
4. Clique **Apply**. Au bout de ~3-5 min, l'app est en ligne sur une URL
   `https://cfc-formulaire-xxxx.onrender.com`.
5. Vérifie : `https://cfc-formulaire-xxxx.onrender.com/api/sante` → `{"ok":true,...}`

## Étape 3 — Récupérer le jeton et brancher l'app interne
1. Render a généré un **SYNC_TOKEN** (Dashboard → service → **Environment**).
   Copie sa valeur.
2. Sur l'app interne CFC, dans le `.env` :
   ```
   CAPTURE_URL=https://crm-cfc-register.com      # (ou l'URL onrender en attendant le domaine)
   CAPTURE_TOKEN=<le SYNC_TOKEN copié depuis Render>
   CAPTURE_AUTO=1
   CAPTURE_INTERVAL_MIN=5
   ```
3. Redémarre l'app interne. Elle capte désormais les soumissions en ligne.

## Étape 4 — Domaine personnalisé
1. Render : service → **Settings** → **Custom Domains** → **Add** `crm-cfc-register.com`
   (et éventuellement `www.crm-cfc-register.com`).
2. Render affiche les enregistrements DNS à créer chez ton registrar :
   - domaine racine : un enregistrement **A** (ou ALIAS) vers l'IP indiquée,
   - `www` : un **CNAME** vers `cfc-formulaire-xxxx.onrender.com`.
3. Une fois le DNS propagé (quelques minutes à quelques heures), Render émet
   automatiquement le **certificat TLS** (HTTPS). 
4. Mets `CAPTURE_URL=https://crm-cfc-register.com` côté interne.

## Étape 5 — Tester
Ouvre `https://crm-cfc-register.com`, remplis le formulaire → le prospect
apparaît sous ~5 min dans **Admin → Captation web** puis en affectation.

---

## ⚠️ Limites du palier gratuit (à connaître)
- **Mise en veille** : le service gratuit s'endort après 15 min d'inactivité ;
  la 1ʳᵉ requête suivante prend ~30 s. Les pulls réguliers de l'app interne le
  maintiennent éveillé en journée. Pour supprimer la veille : plan **Starter**
  (~7 $/mois).
- **PostgreSQL gratuit** : expire après ~30 jours. Pour de vraies données
  clients, prendre une base **payante** (ou Railway/Fly/Neon).
- **RGPD / données personnelles** : ce formulaire collecte des données
  nominatives. Prévoir une mention d'information (déjà présente en bas de page)
  et, pour la prod, l'accord de la conformité CFC.

## Alternative — Railway / Fly.io
- **Railway** : même logique (service + Postgres), pas de mise en veille, mais
  facturation à l'usage après le crédit d'essai.
- **Fly.io** : peut conserver **SQLite** grâce à un volume persistant (`fly volumes`),
  utile si tu préfères éviter Postgres. Demande-moi la config `fly.toml` le cas échéant.
