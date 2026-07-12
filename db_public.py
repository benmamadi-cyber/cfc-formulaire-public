"""
Base de données de l'intermédiaire cloud CFC (formulaire public).

Double backend, choisi automatiquement :
  - PostgreSQL  si la variable DATABASE_URL est définie (plateformes managées
                type Render/Railway/Fly — disque éphémère, il FAUT une base
                persistante externe).
  - SQLite      sinon (développement local, ou VPS avec disque persistant).

Le code applicatif reste identique : il écrit ses requêtes avec des
placeholders « ? » et passe par run() qui les traduit en « %s » pour Postgres.

Cycle de vie d'une soumission :
    nouveau  → (pull par l'app interne) → importe
"""
import os
import sqlite3
import secrets
from datetime import datetime, timezone

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
USE_PG = DATABASE_URL.startswith(('postgres://', 'postgresql://'))

if USE_PG:
    import psycopg
    from psycopg.rows import dict_row
    PH = '%s'
else:
    DB_PATH = os.environ.get('PUBLIC_DB_PATH',
                             os.path.join(os.path.dirname(__file__), 'soumissions.db'))
    PH = '?'


def get_db():
    """Renvoie une connexion (commit/close à la charge de l'appelant)."""
    if USE_PG:
        # psycopg gère postgres:// et postgresql://
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def run(conn, query, params=()):
    """Exécute une requête en traduisant les placeholders « ? » selon le backend.
    Renvoie le curseur. (Aucun « ? » littéral n'apparaît dans nos requêtes.)"""
    if USE_PG:
        query = query.replace('?', PH)
    return conn.execute(query, params)


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


# Schéma — le type de clé primaire auto-incrémentée diffère entre backends.
_PK = 'BIGSERIAL PRIMARY KEY' if USE_PG else 'INTEGER PRIMARY KEY AUTOINCREMENT'

_DDL = f"""
    CREATE TABLE IF NOT EXISTS soumissions(
        id {_PK},
        reference TEXT NOT NULL UNIQUE,
        -- Identité
        nom TEXT NOT NULL,
        prenom TEXT,
        telephone TEXT NOT NULL,
        tel1_whatsapp INTEGER DEFAULT 0,
        telephone2 TEXT,
        tel2_whatsapp INTEGER DEFAULT 0,
        email TEXT,
        nationalite TEXT DEFAULT 'Camerounaise',
        -- Résidence
        pays_residence TEXT,
        pays_residence_code TEXT,
        region TEXT,
        ville TEXT,
        -- Profession (optionnel côté public)
        profession TEXT,
        employeur TEXT,
        revenu_mensuel REAL DEFAULT 0,
        loyers_mensuels REAL DEFAULT 0,
        -- Canal (fixé à 'web' pour ce formulaire)
        canal TEXT DEFAULT 'web',
        canal_sous_type TEXT,
        canal_precise TEXT,
        -- RDV souhaité par le client
        rdv_souhaite INTEGER DEFAULT 0,
        rdv_souhaite_moyen TEXT,
        rdv_souhaite_date TEXT,
        rdv_souhaite_heure TEXT,
        -- Projet
        centres_interets TEXT,
        operation_a_financer TEXT,
        montant_pret_souhaite REAL DEFAULT 0,
        description_besoin TEXT,
        lieu_construction_region TEXT,
        lieu_construction_ville TEXT,
        -- Épargne (optionnel)
        epargne_versement_initial REAL DEFAULT 0,
        epargne_periodicite TEXT,
        epargne_montant_periodique REAL DEFAULT 0,
        epargne_duree_blocage INTEGER DEFAULT 0,
        commentaire TEXT,
        -- Workflow de captation
        statut TEXT DEFAULT 'nouveau',
        cree_le TEXT NOT NULL,
        importe_le TEXT,
        -- Traçabilité anti-abus
        ip TEXT,
        user_agent TEXT
    )
"""


def init_db():
    conn = get_db()
    conn.execute(_DDL)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_soum_statut ON soumissions(statut)")
    conn.commit()
    conn.close()


def generer_reference():
    """Référence lisible remise au prospect : WEB-AAAAMMJJ-XXXX."""
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d')
    suffixe = secrets.token_hex(2).upper()  # 4 caractères
    return f"WEB-{stamp}-{suffixe}"
