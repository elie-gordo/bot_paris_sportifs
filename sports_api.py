"""
Module pour l'API des sports et cotes
Gère la récupération des matchs à venir et des cotes via The Odds API
Inclut un mode démo/fallback pour tester le bot même sans accès API réel
"""

import requests
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportsAPI:
    """Client pour l'API des sports et cotes avec mode démo/fallback"""
    
    def __init__(self, api_key: str, demo_mode: bool = False):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()
        self.demo_mode = demo_mode
        
        if demo_mode:
            logger.info("Mode démo activé - utilisation de données factices")
        
    def _get_demo_sports(self) -> List[Dict]:
        """Retourne des sports de démonstration"""
        return [
            {"key": "soccer_epl", "title": "Premier League", "active": True},
            {"key": "soccer_spain_la_liga", "title": "La Liga", "active": True},
            {"key": "soccer_champions_league", "title": "Champions League", "active": True},
            {"key": "americanfootball_nfl", "title": "NFL", "active": True},
            {"key": "basketball_nba", "title": "NBA", "active": True},
            {"key": "tennis_atp", "title": "ATP Tennis", "active": True},
            {"key": "baseball_mlb", "title": "MLB", "active": True},
            {"key": "icehockey_nhl", "title": "NHL", "active": True}
        ]
    
    def _generate_demo_matches(self, sport_key: str, sport_title: str) -> List[Dict]:
        """Génère des matchs de démonstration pour un sport donné"""
        
        # Équipes par sport
        teams = {
            "soccer_epl": ["Manchester United", "Liverpool", "Manchester City", "Arsenal", "Chelsea", "Tottenham", "Newcastle", "Brighton"],
            "soccer_spain_la_liga": ["Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Real Betis", "Villarreal", "Valencia", "Athletic Bilbao"],
            "soccer_champions_league": ["PSG", "Bayern Munich", "Real Madrid", "Barcelona", "Manchester City", "Liverpool", "AC Milan", "Inter Milan"],
            "americanfootball_nfl": ["Patriots", "Chiefs", "Cowboys", "Packers", "49ers", "Bills", "Dolphins", "Ravens"],
            "basketball_nba": ["Lakers", "Warriors", "Celtics", "Heat", "Bucks", "Nuggets", "Suns", "Nets"],
            "tennis_atp": ["Novak Djokovic", "Carlos Alcaraz", "Daniil Medvedev", "Jannik Sinner", "Andrey Rublev", "Stefanos Tsitsipas"],
            "baseball_mlb": ["Yankees", "Dodgers", "Red Sox", "Giants", "Mets", "Phillies", "Braves", "Astros"],
            "icehockey_nhl": ["Rangers", "Bruins", "Lightning", "Avalanche", "Golden Knights", "Oilers", "Panthers", "Maple Leafs"]
        }
        
        sport_teams = teams.get(sport_key, ["Équipe A", "Équipe B", "Équipe C", "Équipe D"])
        matches = []
        
        # Générer 3-6 matchs pour chaque sport
        num_matches = random.randint(3, 6)
        used_teams = []
        
        for i in range(num_matches):
            # Éviter les doublons d'équipes
            available_teams = [t for t in sport_teams if t not in used_teams]
            if len(available_teams) < 2:
                available_teams = sport_teams.copy()
                used_teams = []
            
            home_team = random.choice(available_teams)
            available_teams.remove(home_team)
            away_team = random.choice(available_teams)
            
            used_teams.extend([home_team, away_team])
            
            # Date/heure dans les 3 prochains jours
            now = datetime.now()
            match_time = now + timedelta(
                days=random.randint(0, 3),
                hours=random.randint(12, 21),
                minutes=random.choice([0, 15, 30, 45])
            )
            
            # Générer des cotes réalistes
            home_odds = random.uniform(1.5, 4.0)
            away_odds = random.uniform(1.5, 4.0)
            draw_odds = random.uniform(2.8, 4.5) if "soccer" in sport_key or "football" in sport_key else None
            
            # Ajuster les cotes pour qu'elles soient cohérentes
            total_prob = (1/home_odds) + (1/away_odds)
            if draw_odds:
                total_prob += (1/draw_odds)
            
            # Normaliser légèrement (bookmaker margin)
            margin = random.uniform(1.05, 1.12)
            home_odds *= margin
            away_odds *= margin
            if draw_odds:
                draw_odds *= margin
            
            # Créer les bookmakers avec des cotes
            bookmakers = []
            bookmaker_names = ["Bet365", "William Hill", "Betfair", "Unibet", "888sport"]
            
            for j, bookie in enumerate(random.sample(bookmaker_names, min(3, len(bookmaker_names)))):
                # Varier légèrement les cotes entre bookmakers
                variation = random.uniform(0.95, 1.05)
                bookie_home = round(home_odds * variation, 2)
                bookie_away = round(away_odds * variation, 2)
                
                outcomes = [
                    {"name": home_team, "price": bookie_home},
                    {"name": away_team, "price": bookie_away}
                ]
                
                if draw_odds:
                    bookie_draw = round(draw_odds * variation, 2)
                    outcomes.append({"name": "Draw", "price": bookie_draw})
                
                bookmaker = {
                    "key": bookie.lower().replace(" ", "_"),
                    "title": bookie,
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": outcomes
                        }
                    ]
                }
                bookmakers.append(bookmaker)
            
            match = {
                "id": f"demo_{sport_key}_{i}_{int(match_time.timestamp())}",
                "sport_key": sport_key,
                "sport_title": sport_title,
                "commence_time": match_time.isoformat() + "Z",
                "home_team": home_team,
                "away_team": away_team,
                "bookmakers": bookmakers
            }
            
            matches.append(match)
        
        return matches
        
    def get_sports(self) -> List[Dict]:
        """Récupère la liste de tous les sports disponibles"""
        if self.demo_mode:
            return self._get_demo_sports()
            
        try:
            url = f"{self.base_url}/sports"
            params = {
                'apiKey': self.api_key
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            sports = response.json()
            logger.info(f"Récupération de {len(sports)} sports disponibles")
            return sports
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des sports: {e}")
            logger.info("Basculement en mode démo")
            self.demo_mode = True
            return self._get_demo_sports()
    
    def get_active_sports(self) -> List[Dict]:
        """Récupère uniquement les sports actifs (avec des matchs en cours)"""
        sports = self.get_sports()
        return [sport for sport in sports if sport.get('active', False)]
    
    def get_odds_for_sport(self, sport_key: str, days_ahead: int = 3) -> List[Dict]:
        """
        Récupère les cotes pour un sport donné
        
        Args:
            sport_key: Clé du sport (ex: 'soccer_epl', 'americanfootball_nfl')
            days_ahead: Nombre de jours à l'avance pour chercher les matchs (défaut: 3)
        """
        if self.demo_mode:
            # Trouver le titre du sport
            sports = self._get_demo_sports()
            sport_title = next((s['title'] for s in sports if s['key'] == sport_key), sport_key)
            return self._generate_demo_matches(sport_key, sport_title)
            
        try:
            url = f"{self.base_url}/sports/{sport_key}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'eu,us',  # Régions européennes et américaines
                'markets': 'h2h',    # Head-to-head (1X2)
                'oddsFormat': 'decimal',
                'dateFormat': 'iso'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            matches = response.json()
            
            # Filtrer les matchs pour les prochains jours
            now = datetime.now()
            end_date = now + timedelta(days=days_ahead)
            
            filtered_matches = []
            for match in matches:
                match_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                if now <= match_time <= end_date:
                    filtered_matches.append(match)
            
            logger.info(f"Sport {sport_key}: {len(filtered_matches)} matchs trouvés pour les {days_ahead} prochains jours")
            return filtered_matches
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des cotes pour {sport_key}: {e}")
            logger.info(f"Basculement en mode démo pour {sport_key}")
            # Basculer temporairement en mode démo pour ce sport
            sports = self._get_demo_sports()
            sport_title = next((s['title'] for s in sports if s['key'] == sport_key), sport_key)
            return self._generate_demo_matches(sport_key, sport_title)
    
    def get_all_upcoming_matches(self, days_ahead: int = 3) -> Dict[str, List[Dict]]:
        """
        Récupère tous les matchs à venir pour tous les sports actifs
        
        Args:
            days_ahead: Nombre de jours à l'avance (défaut: 3, donc J+0 à J+3)
            
        Returns:
            Dictionnaire avec sport_key en clé et liste des matchs en valeur
        """
        all_matches = {}
        active_sports = self.get_active_sports()
        
        logger.info(f"Récupération des matchs pour {len(active_sports)} sports actifs")
        
        for sport in active_sports:
            sport_key = sport['key']
            sport_title = sport['title']
            
            logger.info(f"Récupération des matchs pour {sport_title} ({sport_key})")
            matches = self.get_odds_for_sport(sport_key, days_ahead)
            
            if matches:
                all_matches[sport_key] = {
                    'title': sport_title,
                    'matches': matches
                }
        
        return all_matches
    
    def get_sports_with_matches(self, days_ahead: int = 3) -> Dict[str, List[Dict]]:
        """
        Récupère uniquement les sports qui ont des matchs à venir
        
        Args:
            days_ahead: Nombre de jours à l'avance
            
        Returns:
            Dictionnaire filtré contenant seulement les sports avec des matchs
        """
        all_matches = self.get_all_upcoming_matches(days_ahead)
        return {k: v for k, v in all_matches.items() if v['matches']}
    
    def format_match_info(self, match: Dict) -> str:
        """
        Formate les informations d'un match pour l'affichage
        
        Args:
            match: Dictionnaire contenant les infos du match
            
        Returns:
            String formatée avec les informations du match
        """
        home_team = match['home_team']
        away_team = match['away_team']
        commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
        
        # Récupération des meilleures cotes
        best_odds = self._get_best_odds(match.get('bookmakers', []))
        
        result = f"🆚 {home_team} vs {away_team}\n"
        result += f"🕒 {commence_time.strftime('%d/%m/%Y %H:%M')}\n"
        
        if best_odds:
            result += f"📊 Cotes: {home_team} {best_odds['home']:.2f} | Match nul {best_odds['draw']:.2f} | {away_team} {best_odds['away']:.2f}\n"
        
        return result
    
    def _get_best_odds(self, bookmakers: List[Dict]) -> Optional[Dict]:
        """
        Trouve les meilleures cotes parmi tous les bookmakers
        
        Args:
            bookmakers: Liste des bookmakers avec leurs cotes
            
        Returns:
            Dictionnaire avec les meilleures cotes ou None
        """
        if not bookmakers:
            return None
        
        best_odds = {'home': 0, 'draw': 0, 'away': 0}
        
        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'] == bookmaker.get('home_team', ''):
                            best_odds['home'] = max(best_odds['home'], outcome['price'])
                        elif outcome['name'] == bookmaker.get('away_team', ''):
                            best_odds['away'] = max(best_odds['away'], outcome['price'])
                        elif outcome['name'] == 'Draw':
                            best_odds['draw'] = max(best_odds['draw'], outcome['price'])
        
        return best_odds if best_odds['home'] > 0 else None

# Fonction utilitaire pour créer une instance
def create_sports_api(api_key: str, demo_mode: bool = False) -> SportsAPI:
    """
    Crée une instance de SportsAPI avec la clé API
    
    Args:
        api_key: Clé API pour The Odds API
        demo_mode: Si True, utilise des données de démonstration
    """
    return SportsAPI(api_key, demo_mode)

def create_demo_sports_api() -> SportsAPI:
    """Crée une instance de SportsAPI en mode démo uniquement"""
    return SportsAPI("demo_key", demo_mode=True)
