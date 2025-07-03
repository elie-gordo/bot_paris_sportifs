# Configuration du Bot Paris Sportifs

# Variables d'environnement requises dans .env :
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
# THE_ODDS_API_KEY=your_odds_api_key_here

# Paramètres par défaut
DEFAULT_DAYS_AHEAD = 3  # Chercher les matchs sur J+0 à J+3
MIN_ODDS = 1.5          # Cote minimale pour les analyses
MAX_ODDS = 5.0          # Cote maximale pour les analyses
MIN_CONFIDENCE = 50     # Confiance minimale pour les combinés
COMBO_SIZE = 3          # Taille des combinés
CACHE_TIMEOUT = 300     # Cache de 5 minutes pour éviter les requêtes excessives

# Sports principaux suivis (exemples)
MAIN_SPORTS = [
    'soccer_epl',           # Premier League
    'soccer_france_ligue_one', # Ligue 1
    'soccer_spain_la_liga', # La Liga
    'soccer_italy_serie_a', # Serie A
    'soccer_germany_bundesliga', # Bundesliga
    'americanfootball_nfl', # NFL
    'basketball_nba',       # NBA
    'basketball_euroleague', # Euroleague
    'tennis_atp',           # Tennis ATP
    'tennis_wta'            # Tennis WTA
]

# Régions pour les cotes
ODDS_REGIONS = 'eu,us'  # Europe et États-Unis
ODDS_MARKETS = 'h2h'    # Head-to-head (1X2)
ODDS_FORMAT = 'decimal' # Format décimal européen
