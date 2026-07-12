"""
Référentiels du formulaire public CFC — copie autonome des listes de l'app
interne (constants.py). Volontairement dupliqué : l'intermédiaire cloud ne doit
avoir AUCUNE dépendance vers l'app interne. Si l'app interne fait évoluer ces
listes, resynchroniser ce fichier.

Source : cfc-app/constants.py (VILLES_CAMEROUN, AGENCE_PAR_REGION,
OPERATIONS_A_FINANCER, PAYS_LISTE, MOYENS_RDV_CLIENT).
"""

# Région du Cameroun → villes principales. Pour les régions/pays hors liste,
# la ville reste saisissable en libre.
VILLES_CAMEROUN = {
    'Adamaoua':      ['Ngaoundéré', 'Meiganga', 'Tibati', 'Banyo', 'Tignère'],
    'Centre':        ['Yaoundé', 'Mbalmayo', 'Bafia', 'Obala', 'Nanga-Eboko', 'Mfou', 'Akonolinga', 'Eseka'],
    'Est':           ['Bertoua', 'Batouri', 'Yokadouma', 'Abong-Mbang', 'Belabo'],
    'Extrême-Nord':  ['Maroua', 'Kousseri', 'Mokolo', 'Mora', 'Yagoua', 'Kaélé'],
    'Littoral':      ['Douala', 'Nkongsamba', 'Edéa', 'Loum', 'Manjo', 'Yabassi', 'Mbanga'],
    'Nord':          ['Garoua', 'Guider', 'Figuil', 'Tcholliré', 'Pitoa', 'Poli'],
    'Nord-Ouest':    ['Bamenda', 'Kumbo', 'Wum', 'Nkambé', 'Fundong', 'Mbengwi', 'Batibo'],
    'Ouest':         ['Bafoussam', 'Dschang', 'Foumban', 'Mbouda', 'Bangangté', 'Bandjoun', 'Foumbot'],
    'Sud':           ['Ebolowa', 'Kribi', 'Sangmélima', 'Ambam', 'Mvangan', 'Lolodorf'],
    'Sud-Ouest':     ['Buéa', 'Limbé', 'Tiko', 'Kumba', 'Mamfé', 'Ekondo-Titi', 'Mundemba'],
}

# Région du lieu de construction → code agence CFC (portefeuille).
# NB : le routage définitif est recalculé côté app interne à l'import ; on garde
# la table ici seulement pour information / affichage éventuel.
AGENCE_PAR_REGION = {
    'Centre': '101', 'Littoral': '102', 'Nord': '103', 'Nord-Ouest': '104',
    'Ouest': '105', 'Est': '106', 'Sud': '107', 'Extrême-Nord': '108',
    'Sud-Ouest': '109', 'Adamaoua': '110',
}

REGIONS = list(VILLES_CAMEROUN.keys())

OPERATIONS_A_FINANCER = [
    'Achat de terrain',
    'Construction (terrain disponible)',
    'Acquisition immobilière (terrain + construction)',
    'Acquisition logement existant',
    'Rénovation / Extension',
    'Aménagement / Finitions',
    'Promotion immobilière',
    'Location-vente',
    'Refinancement / Rachat de crédit',
    'Autre (préciser)',
]

MOYENS_RDV_CLIENT = ['Présentiel', 'WhatsApp', 'Téléphone']

PAYS_LISTE = [
    {'code': 'CM', 'fr': 'Cameroun'}, {'code': 'FR', 'fr': 'France'},
    {'code': 'GA', 'fr': 'Gabon'}, {'code': 'CG', 'fr': 'Congo'},
    {'code': 'CD', 'fr': 'République Démocratique du Congo'},
    {'code': 'CF', 'fr': 'République Centrafricaine'}, {'code': 'TD', 'fr': 'Tchad'},
    {'code': 'GQ', 'fr': 'Guinée Équatoriale'}, {'code': 'CI', 'fr': "Côte d'Ivoire"},
    {'code': 'SN', 'fr': 'Sénégal'}, {'code': 'BE', 'fr': 'Belgique'},
    {'code': 'CH', 'fr': 'Suisse'}, {'code': 'CA', 'fr': 'Canada'},
    {'code': 'US', 'fr': 'États-Unis'}, {'code': 'GB', 'fr': 'Royaume-Uni'},
    {'code': 'DE', 'fr': 'Allemagne'}, {'code': 'AUTRE', 'fr': 'Autre'},
]

# Champs métier partagés avec prospects_staging (hors colonnes de workflow).
# L'ordre n'a pas d'importance ; sert de contrat de mapping pour l'API de pull.
CHAMPS_METIER = [
    'nom', 'prenom', 'telephone', 'tel1_whatsapp', 'telephone2', 'tel2_whatsapp',
    'email', 'nationalite', 'pays_residence', 'pays_residence_code', 'region',
    'ville', 'profession', 'employeur', 'revenu_mensuel', 'loyers_mensuels',
    'canal', 'canal_sous_type', 'canal_precise',
    'rdv_souhaite', 'rdv_souhaite_moyen', 'rdv_souhaite_date', 'rdv_souhaite_heure',
    'centres_interets', 'operation_a_financer', 'montant_pret_souhaite',
    'description_besoin', 'lieu_construction_region', 'lieu_construction_ville',
    'epargne_versement_initial', 'epargne_periodicite', 'epargne_montant_periodique',
    'epargne_duree_blocage', 'commentaire',
]
