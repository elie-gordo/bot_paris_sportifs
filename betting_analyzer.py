"""
Module d'analyse des paris et génération de combinés
Analyse les cotes et propose des stratégies de paris automatiques
"""

import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BettingAnalyzer:
    """Analyseur de paris sportifs et générateur de combinés"""
    
    def __init__(self, min_odds: float = 1.5, max_odds: float = 5.0):
        """
        Initialise l'analyseur
        
        Args:
            min_odds: Cote minimale à considérer
            max_odds: Cote maximale à considérer
        """
        self.min_odds = min_odds
        self.max_odds = max_odds
    
    def analyze_match(self, match: Dict) -> Dict:
        """
        Analyse un match et donne des recommandations détaillées
        
        Args:
            match: Dictionnaire contenant les infos du match
            
        Returns:
            Dictionnaire avec l'analyse complète du match
        """
        home_team = match['home_team']
        away_team = match['away_team']
        commence_time = match.get('commence_time', '')
        
        # Récupération des meilleures cotes
        best_odds = self._get_best_odds_from_match(match)
        
        if not best_odds:
            return {
                'match': f"{home_team} vs {away_team}",
                'recommendation': 'Aucune cote disponible',
                'confidence': 0,
                'value_bet': False,
                'risk_level': 'Unknown',
                'match_time': commence_time
            }
        
        # Calcul des probabilités implicites
        probs = self._calculate_probabilities(best_odds)
        
        # Analyse des tendances et choix du meilleur pari
        analysis_result = self._analyze_best_bet(best_odds, probs, home_team, away_team)
        
        # Détection de value bet
        is_value = self._is_value_bet(best_odds, probs)
        
        # Calcul du niveau de risque
        risk_level = self._calculate_risk_level(analysis_result['recommended_odds'])
        
        # Calcul de confiance amélioré
        confidence = self._calculate_enhanced_confidence(analysis_result, best_odds, is_value)
        
        return {
            'match': f"{home_team} vs {away_team}",
            'recommendation': f"{analysis_result['recommendation']} (cote: {analysis_result['recommended_odds']:.2f})",
            'confidence': confidence,
            'value_bet': is_value,
            'risk_level': risk_level,
            'match_time': commence_time,
            'all_odds': best_odds,
            'probabilities': probs
        }
    
    def _analyze_best_bet(self, odds: Dict, probs: Dict, home_team: str, away_team: str) -> Dict:
        """Analyse et détermine le meilleur pari"""
        options = []
        
        # Analyser chaque option
        if odds.get('home', 0) > 0:
            value_score = (probs.get('home', 0) * odds['home']) - 1
            options.append({
                'type': 'home',
                'team': home_team,
                'odds': odds['home'],
                'probability': probs.get('home', 0),
                'value_score': value_score,
                'recommendation': f"Victoire {home_team}"
            })
        
        if odds.get('away', 0) > 0:
            value_score = (probs.get('away', 0) * odds['away']) - 1
            options.append({
                'type': 'away',
                'team': away_team,
                'odds': odds['away'],
                'probability': probs.get('away', 0),
                'value_score': value_score,
                'recommendation': f"Victoire {away_team}"
            })
        
        if odds.get('draw', 0) > 0:
            value_score = (probs.get('draw', 0) * odds['draw']) - 1
            options.append({
                'type': 'draw',
                'team': 'Match nul',
                'odds': odds['draw'],
                'probability': probs.get('draw', 0),
                'value_score': value_score,
                'recommendation': "Match nul"
            })
        
        # Choisir la meilleure option (équilibre entre probabilité et value)
        if options:
            # Pondération : 60% probabilité, 40% value score
            for option in options:
                option['combined_score'] = (option['probability'] * 0.6) + (max(0, option['value_score']) * 0.4)
            
            best_option = max(options, key=lambda x: x['combined_score'])
            return {
                'recommendation': best_option['recommendation'],
                'recommended_odds': best_option['odds'],
                'probability': best_option['probability'],
                'value_score': best_option['value_score'],
                'type': best_option['type']
            }
        
        return {
            'recommendation': f"Victoire {home_team}",
            'recommended_odds': odds.get('home', 2.0),
            'probability': probs.get('home', 0.4),
            'value_score': 0,
            'type': 'home'
        }
    
    def _calculate_enhanced_confidence(self, analysis: Dict, odds: Dict, is_value: bool) -> int:
        """Calcule un niveau de confiance amélioré"""
        base_confidence = analysis['probability'] * 100
        
        # Bonus pour value bet
        if is_value:
            base_confidence += 10
        
        # Ajustement selon les cotes
        recommended_odds = analysis['recommended_odds']
        if recommended_odds < 1.5:
            base_confidence += 20  # Bonus pour les favoris
        elif recommended_odds > 4.0:
            base_confidence -= 15  # Malus pour les outsiders
        
        # Ajustement selon le value score
        if analysis['value_score'] > 0.1:
            base_confidence += 15
        elif analysis['value_score'] < -0.1:
            base_confidence -= 10
        
        # Normaliser entre 0 et 100
        confidence = max(0, min(100, int(base_confidence)))
        
        return confidence
    
    def _calculate_risk_level(self, odds: float) -> str:
        """Calcule le niveau de risque basé sur les cotes"""
        if odds < 2.0:
            return "Faible"
        elif odds < 3.5:
            return "Moyen"
        else:
            return "Élevé"
        analysis = self._analyze_odds(best_odds, home_team, away_team)
        
        return {
            'match': f"{home_team} vs {away_team}",
            'odds': best_odds,
            'recommendation': analysis['recommendation'],
            'confidence': analysis['confidence'],
            'value_bet': analysis['value_bet'],
            'commence_time': match['commence_time']
        }
    
    def _get_best_odds_from_match(self, match: Dict) -> Optional[Dict]:
        """Extrait les meilleures cotes d'un match"""
        if not match.get('bookmakers'):
            return None
        
        best_odds = {'home': 0, 'draw': 0, 'away': 0}
        home_team = match['home_team']
        away_team = match['away_team']
        
        for bookmaker in match['bookmakers']:
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team:
                            best_odds['home'] = max(best_odds['home'], outcome['price'])
                        elif outcome['name'] == away_team:
                            best_odds['away'] = max(best_odds['away'], outcome['price'])
                        elif outcome['name'] == 'Draw':
                            best_odds['draw'] = max(best_odds['draw'], outcome['price'])
        
        return best_odds if best_odds['home'] > 0 else None
    
    def _analyze_odds(self, odds: Dict, home_team: str, away_team: str) -> Dict:
        """
        Analyse les cotes et donne une recommandation
        
        Args:
            odds: Dictionnaire avec les cotes
            home_team: Nom de l'équipe à domicile
            away_team: Nom de l'équipe à l'extérieur
        """
        home_odds = odds['home']
        draw_odds = odds['draw']
        away_odds = odds['away']
        
        # Calcul des probabilités implicites
        home_prob = 1 / home_odds if home_odds > 0 else 0
        draw_prob = 1 / draw_odds if draw_odds > 0 else 0
        away_prob = 1 / away_odds if away_odds > 0 else 0
        
        total_prob = home_prob + draw_prob + away_prob
        
        # Normalisation des probabilités
        if total_prob > 0:
            home_prob_norm = home_prob / total_prob
            draw_prob_norm = draw_prob / total_prob
            away_prob_norm = away_prob / total_prob
        else:
            return {
                'recommendation': 'Cotes invalides',
                'confidence': 0,
                'value_bet': False
            }
        
        # Détermination du favori
        probs = {
            'home': home_prob_norm,
            'draw': draw_prob_norm,
            'away': away_prob_norm
        }
        
        favorite = max(probs, key=probs.get)
        max_prob = probs[favorite]
        
        # Génération de la recommandation
        if favorite == 'home':
            recommendation = f"Victoire {home_team} (cote: {home_odds:.2f})"
            confidence = int(home_prob_norm * 100)
        elif favorite == 'away':
            recommendation = f"Victoire {away_team} (cote: {away_odds:.2f})"
            confidence = int(away_prob_norm * 100)
        else:
            recommendation = f"Match nul (cote: {draw_odds:.2f})"
            confidence = int(draw_prob_norm * 100)
        
        # Détection des value bets (cotes intéressantes)
        value_bet = self._is_value_bet(odds, probs)
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'value_bet': value_bet
        }
    
    def _is_value_bet(self, odds: Dict, probs: Dict) -> bool:
        """
        Détermine si un pari représente une valeur intéressante
        
        Args:
            odds: Cotes du match
            probs: Probabilités normalisées
        """
        # Critères simples pour détecter une value bet
        # Cote entre min_odds et max_odds ET probabilité > 30%
        for outcome, prob in probs.items():
            if outcome == 'home':
                if self.min_odds <= odds['home'] <= self.max_odds and prob > 0.3:
                    return True
            elif outcome == 'away':
                if self.min_odds <= odds['away'] <= self.max_odds and prob > 0.3:
                    return True
            elif outcome == 'draw':
                if self.min_odds <= odds['draw'] <= self.max_odds and prob > 0.25:
                    return True
        
        return False
    
    def generate_combinations(self, analyses: List[Dict], combo_size: int = 3) -> List[Dict]:
        """
        Génère des combinés à partir des analyses de matchs
        
        Args:
            analyses: Liste des analyses de matchs
            combo_size: Taille des combinés (défaut: 3)
            
        Returns:
            Liste des combinés recommandés
        """
        if len(analyses) < combo_size:
            logger.warning(f"Pas assez de matchs pour un combiné de {combo_size}")
            return []
        
        # Filtrer les matchs avec une confiance minimale
        good_bets = [analysis for analysis in analyses if analysis['confidence'] >= 50]
        
        if len(good_bets) < combo_size:
            logger.warning(f"Pas assez de paris fiables pour un combiné de {combo_size}")
            return []
        
        # Générer plusieurs combinés
        combinations = []
        
        # Combiné "Sûr" - paris avec la plus haute confiance
        safe_combo = sorted(good_bets, key=lambda x: x['confidence'], reverse=True)[:combo_size]
        combinations.append(self._create_combination(safe_combo, "Combiné Sûr"))
        
        # Combiné "Value" - paris avec des value bets
        value_bets = [bet for bet in good_bets if bet['value_bet']]
        if len(value_bets) >= combo_size:
            combinations.append(self._create_combination(value_bets[:combo_size], "Combiné Value"))
        
        # Combiné "Mixte" - mélange aléatoire des bons paris
        if len(good_bets) >= combo_size:
            random.shuffle(good_bets)
            combinations.append(self._create_combination(good_bets[:combo_size], "Combiné Mixte"))
        
        return combinations
    
    def _create_combination(self, bets: List[Dict], combo_type: str) -> Dict:
        """
        Crée un combiné à partir d'une liste de paris
        
        Args:
            bets: Liste des paris à combiner
            combo_type: Type de combiné
            
        Returns:
            Dictionnaire représentant le combiné
        """
        total_odds = 1.0
        total_confidence = 0
        matches = []
        
        for bet in bets:
            # Extraction de la cote de la recommandation
            odds_str = bet['recommendation'].split('(cote: ')[1].split(')')[0]
            odds = float(odds_str)
            total_odds *= odds
            total_confidence += bet['confidence']
            
            matches.append({
                'match': bet['match'],
                'bet': bet['recommendation'],
                'confidence': bet['confidence']
            })
        
        avg_confidence = total_confidence / len(bets)
        
        return {
            'type': combo_type,
            'matches': matches,
            'total_odds': round(total_odds, 2),
            'avg_confidence': round(avg_confidence),
            'potential_return': f"Pour 10€ → {round(total_odds * 10, 2)}€"
        }
    
    def format_combination(self, combination: Dict) -> str:
        """
        Formate un combiné pour l'affichage
        
        Args:
            combination: Dictionnaire du combiné
            
        Returns:
            String formatée du combiné
        """
        result = f"🎯 {combination['type']}\n"
        result += f"📈 Cote totale: {combination['total_odds']}\n"
        result += f"🎲 Confiance moyenne: {combination['avg_confidence']}%\n"
        result += f"💰 {combination['potential_return']}\n\n"
        
        result += "📋 Détail des paris:\n"
        for i, match in enumerate(combination['matches'], 1):
            result += f"{i}. {match['match']}\n"
            result += f"   ➤ {match['bet']} (confiance: {match['confidence']}%)\n"
        
        return result
    
    def generate_specific_combination(self, analyses: List[Dict], level: str) -> Dict:
        """
        Génère un combiné spécifique selon le niveau de risque
        
        Args:
            analyses: Liste des analyses de matchs
            level: Niveau de risque (SAFE, MOYEN, HIGH_RISK)
            
        Returns:
            Dictionnaire du combiné ou None si impossible
        """
        if len(analyses) < 3:
            logger.warning(f"Pas assez de matchs pour un combiné {level}")
            return None
        
        # Configuration par niveau
        level_configs = {
            "SAFE": {
                "min_confidence": 75,
                "combo_size": 3,
                "sort_by": "confidence",  # Trier par confiance
                "desc": True
            },
            "MOYEN": {
                "min_confidence": 60,
                "combo_size": 4,
                "sort_by": "confidence",
                "desc": True
            },
            "HIGH_RISK": {
                "min_confidence": 45,
                "combo_size": 5,
                "sort_by": "odds",  # Trier par cotes (plus risqué)
                "desc": True
            }
        }
        
        config = level_configs.get(level, level_configs["MOYEN"])
        
        # Filtrer selon le niveau
        filtered_bets = [bet for bet in analyses if bet['confidence'] >= config['min_confidence']]
        
        if len(filtered_bets) < 3:
            # Si pas assez, prendre les meilleurs disponibles
            filtered_bets = sorted(analyses, key=lambda x: x['confidence'], reverse=True)[:config['combo_size']]
        
        # Trier selon la stratégie du niveau
        if config['sort_by'] == 'confidence':
            selected_bets = sorted(filtered_bets, key=lambda x: x['confidence'], reverse=config['desc'])
        else:  # sort by odds
            selected_bets = []
            for bet in filtered_bets:
                try:
                    odds_str = bet['recommendation'].split('(cote: ')[1].split(')')[0]
                    odds = float(odds_str)
                    bet['_extracted_odds'] = odds
                    selected_bets.append(bet)
                except:
                    bet['_extracted_odds'] = 2.0  # Valeur par défaut
                    selected_bets.append(bet)
            
            selected_bets = sorted(selected_bets, key=lambda x: x['_extracted_odds'], reverse=config['desc'])
        
        # Prendre le nombre requis
        final_bets = selected_bets[:min(config['combo_size'], len(selected_bets))]
        
        # Créer le combiné
        combo_type_names = {
            "SAFE": "Combiné SAFE 🛡️",
            "MOYEN": "Combiné MOYEN ⚖️", 
            "HIGH_RISK": "Combiné HIGH RISK 🚀"
        }
        
        return self._create_combination(final_bets, combo_type_names[level])

    def _calculate_probabilities(self, odds: Dict) -> Dict:
        """
        Calcule les probabilités implicites à partir des cotes
        
        Args:
            odds: Dictionnaire des meilleures cotes
            
        Returns:
            Dictionnaire des probabilités normalisées
        """
        probs = {}
        total_prob = 0
        
        # Calcul des probabilités brutes (1/cote)
        if odds.get('home', 0) > 0:
            probs['home'] = 1 / odds['home']
            total_prob += probs['home']
        
        if odds.get('away', 0) > 0:
            probs['away'] = 1 / odds['away']
            total_prob += probs['away']
        
        if odds.get('draw', 0) > 0:
            probs['draw'] = 1 / odds['draw']
            total_prob += probs['draw']
        
        # Normalisation pour supprimer la marge du bookmaker
        if total_prob > 0:
            for key in probs:
                probs[key] = probs[key] / total_prob
        
        return probs

# Fonction utilitaire pour créer un analyseur
def create_betting_analyzer(min_odds: float = 1.5, max_odds: float = 5.0) -> BettingAnalyzer:
    """Crée une instance de BettingAnalyzer"""
    return BettingAnalyzer(min_odds, max_odds)