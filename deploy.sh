#!/bin/bash
# ============================================================
#  CFC — Formulaire public d'auto-enregistrement des prospects
#  Déploiement Linux (Ubuntu/Debian) sur le VPS « CAFCA »
#  Usage : chmod +x deploy.sh && sudo ./deploy.sh
#
#  Idempotent : ré-exécutable. Ne régénère PAS le SYNC_TOKEN ni le .env
#  s'ils existent déjà (sinon la liaison avec l'app interne serait cassée).
# ============================================================
set -euo pipefail

APP_DIR=/opt/cfc-formulaire
ENV_FILE="$APP_DIR/.env"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_NAME="${CFC_FORM_SERVER_NAME:-formulaire.creditfoncier.cm}"

echo "=================================================="
echo "  CFC — Déploiement formulaire public"
echo "=================================================="

# ── 1. Paquets système ──────────────────────────────────────────────────────
echo "[1/6] Paquets système (Python, Nginx, rsync)…"
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv nginx rsync -qq

# ── 2. Copie des fichiers (préserve .env et la base existants) ───────────────
echo "[2/6] Copie vers $APP_DIR…"
mkdir -p "$APP_DIR"
rsync -a --exclude='.env' --exclude='*.db' --exclude='*.db-*' \
      --exclude='venv' --exclude='.git' --exclude='__pycache__' \
      "$SRC_DIR"/ "$APP_DIR"/
cd "$APP_DIR"

# ── 3. venv + dépendances ────────────────────────────────────────────────────
echo "[3/6] venv + dépendances…"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

# ── 4. .env (SYNC_TOKEN généré UNE fois) ─────────────────────────────────────
echo "[4/6] Configuration .env…"
if [ ! -f "$ENV_FILE" ]; then
  TOKEN="$(./venv/bin/python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  cat > "$ENV_FILE" << EOF
# Généré au déploiement — NE PAS COMMITTER.
# ⚠️  Reporter EXACTEMENT ce SYNC_TOKEN dans le .env de l'app interne
#     sous le nom CAPTURE_TOKEN.
SYNC_TOKEN=$TOKEN
PUBLIC_DB_PATH=$APP_DIR/soumissions.db
PORT=8080
RATE_SOUMISSION=5 per hour
EOF
  chmod 600 "$ENV_FILE"
  echo ""
  echo "  ┌────────────────────────────────────────────────────────────┐"
  echo "  │  SYNC_TOKEN généré. À copier dans le .env de l'app interne : │"
  echo "  │  CAPTURE_TOKEN=$TOKEN"
  echo "  └────────────────────────────────────────────────────────────┘"
  echo ""
else
  echo "  .env déjà présent — inchangé."
fi
chown -R www-data:www-data "$APP_DIR"

# ── 5. Service systemd ───────────────────────────────────────────────────────
echo "[5/6] Service systemd…"
cp deploy/cfc-formulaire.service /etc/systemd/system/cfc-formulaire.service
systemctl daemon-reload
systemctl enable cfc-formulaire
systemctl restart cfc-formulaire

# ── 6. Nginx + TLS ───────────────────────────────────────────────────────────
echo "[6/6] Nginx (reverse proxy)…"
sed "s/formulaire.creditfoncier.cm/$SERVER_NAME/g" \
    deploy/nginx-cfc-formulaire.conf > /etc/nginx/sites-available/cfc-formulaire
ln -sf /etc/nginx/sites-available/cfc-formulaire /etc/nginx/sites-enabled/cfc-formulaire
nginx -t && systemctl reload nginx

echo ""
echo "✔ Déploiement terminé."
echo "  Prochaine étape TLS (Let's Encrypt) :"
echo "    sudo apt-get install -y certbot python3-certbot-nginx"
echo "    sudo certbot --nginx -d $SERVER_NAME"
echo ""
echo "  Vérifier : curl https://$SERVER_NAME/api/sante"
