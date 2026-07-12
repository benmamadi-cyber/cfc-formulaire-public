"""
Intermédiaire cloud CFC — formulaire public d'auto-enregistrement des prospects.

À DÉPLOYER SUR LE VPS PUBLIC (« CAFCA »), séparément de l'application interne.

Rôles :
  1. Servir le formulaire public (étape 1 du parcours prospect).
  2. Recevoir les soumissions (POST /api/soumission) — public, anti-spam.
  3. Exposer les soumissions à l'app interne (GET /api/soumissions) — protégé
     par un jeton Bearer, sur le modèle de la passerelle NEXAH.
  4. Marquer une soumission consommée (POST /api/soumissions/<id>/consomme).

Sécurité :
  - Les endpoints de synchronisation exigent le header
    « Authorization: Bearer <SYNC_TOKEN> ».
  - Le POST public est limité en débit (anti-flood) + honeypot anti-bot.
  - Aucune donnée sensible obligatoire ; validation stricte du téléphone.
"""
import os
import logging
from functools import wraps

# Charge un éventuel .env local (sans écraser les variables déjà définies par
# le système/systemd). En production, systemd injecte l'env via EnvironmentFile.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, request, jsonify, render_template, abort

from db_public import get_db, run, init_db, now_iso, generer_reference
import referentiels as ref

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cfc-public')

app = Flask(__name__)

# Jeton partagé avec l'app interne pour le pull. En prod : le définir en env.
SYNC_TOKEN = os.environ.get('SYNC_TOKEN', '')

# Limitation de débit optionnelle (si flask-limiter est installé).
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(get_remote_address, app=app, default_limits=[])
    RATE_SOUMISSION = os.environ.get('RATE_SOUMISSION', '5 per hour')
except Exception:  # flask-limiter absent → pas de limite (dev)
    limiter = None
    RATE_SOUMISSION = None


# ─── Sécurité des endpoints de synchronisation ─────────────────────────────
def exiger_token(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not SYNC_TOKEN:
            logger.error('SYNC_TOKEN non configuré : endpoint de pull désactivé.')
            abort(503)
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer ') or auth[7:].strip() != SYNC_TOKEN:
            abort(401)
        return f(*a, **kw)
    return wrapper


# ─── Formulaire public ─────────────────────────────────────────────────────
@app.route('/')
def formulaire():
    return render_template(
        'formulaire.html',
        villes=ref.VILLES_CAMEROUN,
        regions=ref.REGIONS,
        pays=ref.PAYS_LISTE,
        operations=ref.OPERATIONS_A_FINANCER,
        moyens_rdv=ref.MOYENS_RDV_CLIENT,
    )


def _bad(msg, code=400):
    return jsonify({'ok': False, 'msg': msg}), code


def _soumission_impl():
    data = request.form if request.form else (request.json or {})

    def s(k, d=''):
        return str(data.get(k, d) or d).strip()
    def iv(k, d=0):
        try: return int(data.get(k) or d)
        except (TypeError, ValueError): return d
    def fv(k, d=0):
        try: return float(str(data.get(k) or d).replace(' ', '').replace(',', '.'))
        except (TypeError, ValueError): return d

    # Honeypot : champ invisible qui ne doit jamais être rempli par un humain.
    if s('site_web_confirm'):
        logger.info('Honeypot déclenché — soumission ignorée (bot probable).')
        return jsonify({'ok': True, 'reference': 'IGNORE'})  # on ne révèle rien

    # ── Validations minimales (miroir de /api/prospects/etape1) ──
    nom, prenom, tel = s('nom'), s('prenom'), s('telephone')
    if not nom or not prenom:
        return _bad('Nom et prénom sont obligatoires.')
    tel_norm = tel.replace(' ', '')
    if not (tel_norm.startswith('6') and len(tel_norm) == 9 and tel_norm.isdigit()):
        return _bad('Numéro de téléphone invalide (format attendu : 6 suivi de 8 chiffres).')

    centres = [c for c in ('pret', 'epargne') if iv(f'centre_{c}')]
    if not centres:
        return _bad("Sélectionnez au moins un centre d'intérêt (prêt et/ou épargne).")

    lcr = s('lieu_construction_region')
    if 'pret' in centres and not lcr:
        return _bad("Indiquez la région du lieu de votre projet.")

    email = s('email')
    if email and ('@' not in email or '.' not in email.split('@')[-1]):
        return _bad('Adresse e-mail invalide.')

    reference = generer_reference()
    ligne = dict(
        reference=reference,
        nom=nom, prenom=prenom,
        telephone=tel_norm, tel1_whatsapp=iv('tel1_whatsapp'),
        telephone2=s('telephone2').replace(' ', ''), tel2_whatsapp=iv('tel2_whatsapp'),
        email=email,
        nationalite=s('nationalite', 'Camerounaise'),
        pays_residence=s('pays_residence', 'Cameroun'),
        pays_residence_code=s('pays_residence_code', 'CM'),
        region=s('region'),
        ville=s('ville'),
        profession=s('profession'),
        employeur=s('employeur'),
        revenu_mensuel=fv('revenu_mensuel'),
        loyers_mensuels=fv('loyers_mensuels'),
        canal='web',
        canal_sous_type='Site CFC',
        canal_precise="Formulaire en ligne d'auto-enregistrement",
        rdv_souhaite=iv('rdv_souhaite'),
        rdv_souhaite_moyen=s('rdv_souhaite_moyen'),
        rdv_souhaite_date=s('rdv_souhaite_date'),
        rdv_souhaite_heure=s('rdv_souhaite_heure'),
        centres_interets=','.join(centres),
        operation_a_financer=s('operation_a_financer'),
        montant_pret_souhaite=fv('montant_pret_souhaite'),
        description_besoin=s('description_besoin'),
        lieu_construction_region=lcr,
        lieu_construction_ville=s('lieu_construction_ville'),
        epargne_versement_initial=fv('epargne_versement_initial'),
        epargne_periodicite=s('epargne_periodicite'),
        epargne_montant_periodique=fv('epargne_montant_periodique'),
        epargne_duree_blocage=iv('epargne_duree_blocage'),
        commentaire=s('commentaire'),
        statut='nouveau',
        cree_le=now_iso(),
        ip=request.headers.get('X-Forwarded-For', request.remote_addr or ''),
        user_agent=(request.headers.get('User-Agent', '') or '')[:300],
    )
    conn = get_db()
    cols = ','.join(ligne.keys())
    ph = ','.join('?' * len(ligne))
    run(conn, f"INSERT INTO soumissions({cols}) VALUES({ph})", list(ligne.values()))
    conn.commit(); conn.close()
    logger.info('Nouvelle soumission %s (%s %s)', reference, nom, prenom)
    return jsonify({'ok': True, 'reference': reference,
                    'msg': "Votre demande a bien été enregistrée."})


@app.route('/api/soumission', methods=['POST'])
def soumission():
    return _soumission_impl()


# Applique la limitation de débit si flask-limiter est disponible.
if limiter is not None:
    soumission = app.view_functions['soumission'] = limiter.limit(RATE_SOUMISSION)(_soumission_impl)


# ─── Endpoints de pull (app interne) ───────────────────────────────────────
@app.route('/api/soumissions', methods=['GET'])
@exiger_token
def lister_soumissions():
    """Renvoie les soumissions au statut 'nouveau' (ou > since)."""
    try:
        since = int(request.args.get('since', 0))
    except (TypeError, ValueError):
        since = 0
    limit = min(int(request.args.get('limit', 100) or 100), 500)
    conn = get_db()
    rows = run(conn,
        "SELECT * FROM soumissions WHERE statut='nouveau' AND id > ? "
        "ORDER BY id ASC LIMIT ?", (since, limit)).fetchall()
    conn.close()
    return jsonify({'ok': True, 'count': len(rows),
                    'soumissions': [dict(r) for r in rows]})


@app.route('/api/soumissions/<int:sid>/consomme', methods=['POST'])
@exiger_token
def consommer(sid):
    """Marque une soumission comme importée (idempotent)."""
    conn = get_db()
    row = run(conn, "SELECT statut FROM soumissions WHERE id=?", (sid,)).fetchone()
    if not row:
        conn.close(); return _bad('Soumission introuvable.', 404)
    run(conn, "UPDATE soumissions SET statut='importe', importe_le=? WHERE id=?",
        (now_iso(), sid))
    conn.commit(); conn.close()
    return jsonify({'ok': True})


@app.route('/api/sante', methods=['GET'])
def sante():
    return jsonify({'ok': True, 'service': 'cfc-formulaire-public'})


# Création idempotente du schéma au démarrage. Indispensable sous gunicorn
# (plateformes managées) où le bloc __main__ n'est jamais exécuté.
try:
    init_db()
except Exception as _exc:  # pragma: no cover
    logger.warning('init_db au démarrage impossible (réessai au 1er accès) : %s', _exc)


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    print(f"Formulaire public CFC démarré sur http://0.0.0.0:{port}")
    if not SYNC_TOKEN:
        print("⚠️  SYNC_TOKEN non défini : les endpoints de pull renverront 503.")
    app.run(host='0.0.0.0', port=port, debug=False)
