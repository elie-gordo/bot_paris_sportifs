"""
BetIQ 2.5 - Bot Telegram pour les paris sportifs
Bot principal qui gère les commandes Telegram et orchestre l'analyse des matchs
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Set
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)
from dotenv import load_dotenv

from sports_api import create_sports_api
from betting_analyzer import create_betting_analyzer
import config

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

class BetIQ25Bot:
    """BetIQ 2.5 - Bot Telegram pour les paris sportifs"""
    
    def __init__(self, demo_mode: bool = False):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.odds_api_key = os.getenv('THE_ODDS_API_KEY')
        self.demo_mode = demo_mode
        
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN manquant dans le fichier .env")
        
        if not self.odds_api_key and not demo_mode:
            logger.warning("THE_ODDS_API_KEY manquant - basculement en mode démo")
            self.demo_mode = True
        
        self.sports_api = create_sports_api(self.odds_api_key or "demo", self.demo_mode)
        self.betting_analyzer = create_betting_analyzer(config.MIN_ODDS, config.MAX_ODDS)
        
        # Cache pour éviter trop de requêtes API
        self.cache = {}
        self.cache_timeout = config.CACHE_TIMEOUT
        
        # Système de tracking des utilisateurs
        self.users_file = Path("known_users.json")
        self.known_users: Set[int] = self._load_known_users()
    
    def _load_known_users(self) -> Set[int]:
        """Charge la liste des utilisateurs connus depuis le fichier"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('users', []))
        except Exception as e:
            logger.warning(f"Erreur lors du chargement des utilisateurs connus: {e}")
        return set()
    
    def _save_known_users(self):
        """Sauvegarde la liste des utilisateurs connus"""
        try:
            data = {
                'users': list(self.known_users),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde des utilisateurs connus: {e}")
    
    def _is_new_user(self, user_id: int) -> bool:
        """Vérifie si c'est un nouvel utilisateur"""
        return user_id not in self.known_users
    
    def _register_user(self, user_id: int):
        """Enregistre un nouvel utilisateur"""
        if user_id not in self.known_users:
            self.known_users.add(user_id)
            self._save_known_users()
            logger.info(f"Nouvel utilisateur enregistré: {user_id}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start - Message d'accueil avec logo et boutons cliquables en un seul message"""
        user_name = update.effective_user.first_name if update.effective_user else "Utilisateur"
        
        # Préparer le message de bienvenue
        welcome_message = f"""🎯 **BetIQ 2.5** 🎯

Bienvenue {user_name} ! Votre assistant intelligent pour les paris sportifs.

**🚀 Fonctionnalités :**
• 🔍 Recherche automatique sur tous les sports
• 📊 Cotes en temps réel et analyses IA
• 🧠 Analyses automatiques avancées
• 🎲 Génération de combinés intelligents
• 💎 Détection des value bets
• 📈 Statistiques et recommandations

**Cliquez sur un bouton ci-dessous pour commencer :**"""
        
        # Ajouter une notification si en mode démo
        if self.demo_mode:
            welcome_message += "\n\n⚠️ **Mode Démo** : Utilisation de données factices pour démonstration"
        
        # Créer les boutons cliquables pour les commandes principales
        keyboard = [
            [InlineKeyboardButton("🔍 Voir tous les matchs", callback_data="cmd_matches")],
            [InlineKeyboardButton("📊 Analyse complète", callback_data="cmd_analysis")],
            [InlineKeyboardButton("🎲 Générer des combinés", callback_data="cmd_combos")],
            [InlineKeyboardButton("⚽ Sports disponibles", callback_data="cmd_sports")],
            [InlineKeyboardButton("❓ Aide détaillée", callback_data="cmd_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Essayer d'envoyer avec le logo en premier (PNG ou JPG)
        try:
            # Chercher d'abord le fichier PNG, puis JPG
            logo_path = None
            for extension in ['png', 'jpg', 'jpeg']:
                test_path = Path(f"logo_betiq.{extension}")
                if test_path.exists() and test_path.stat().st_size > 1000:  # Vérifier que le fichier fait plus de 1KB
                    logo_path = test_path
                    break
            
            if logo_path:
                # Envoyer le logo avec le message complet et les boutons en une seule fois
                with open(logo_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=welcome_message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                return  # Important : sortir ici pour éviter d'envoyer deux messages
        except Exception as e:
            logger.warning(f"Impossible d'envoyer le logo avec le message: {e}")
        
        # Si pas de logo ou erreur, envoyer avec logo ASCII en un seul message
        logo_ascii = """```
╔══════════════════════════════════╗
║         🎯 BetIQ 2.5 🎯          ║
║    ┌─────────────────────────┐   ║
║    │  📊 AI BETTING BOT 🤖  │   ║
║    └─────────────────────────┘   ║
║  💎 Intelligence • Analytics 📈  ║
╚══════════════════════════════════╝
```

"""
        
        # Combiner le logo ASCII avec le message de bienvenue
        complete_message = logo_ascii + welcome_message
        
        await update.message.reply_text(
            complete_message, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help - Aide détaillée"""
        # Déterminer la méthode d'envoi selon le type d'update
        if update.message:
            send_message = update.message.reply_text
        elif update.callback_query:
            send_message = update.callback_query.message.reply_text
        else:
            logger.error("Update sans message ni callback_query")
            return
        
        help_text = """
📖 **Aide détaillée - BetIQ 2.5**

**Commandes principales :**
• `/start` - Message d'accueil avec logo
• `/matches` - Liste tous les matchs à venir sur tous les sports
• `/analysis` - Analyse détaillée des meilleurs matchs
• `/combos` - Génère 3 types de combinés automatiquement
• `/sports` - Affiche tous les sports suivis

**Comment ça marche :**
1. BetIQ 2.5 cherche automatiquement les matchs de J+0 à J+3
2. Il analyse les cotes de tous les bookmakers avec IA
3. Il propose des recommandations basées sur les probabilités
4. Il génère des combinés optimisés par niveau de risque

**Types de combinés :**
🛡️ **SAFE** - Paris avec la plus haute confiance (≥75%)
⚖️ **MOYEN** - Paris équilibrés risque/rendement (≥60%)
🚀 **HIGH RISK** - Paris à fort potentiel (≥45%)

**Value Bets :** Paris où les cotes semblent sous-évaluées par les bookmakers.
        """
        
        await send_message(help_text, parse_mode='Markdown')
    
    async def sports_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /sports - Liste des sports disponibles"""
        # Déterminer la méthode d'envoi selon le type d'update
        if update.message:
            send_message = update.message.reply_text
        elif update.callback_query:
            send_message = update.callback_query.message.reply_text
        else:
            logger.error("Update sans message ni callback_query")
            return
        
        await send_message("🔍 Récupération des sports disponibles...")
        
        try:
            sports = self.sports_api.get_active_sports()
            
            if not sports:
                await send_message("❌ Aucun sport disponible actuellement.")
                return
            
            message = "⚽ **Sports disponibles :**\n\n"
            for sport in sports[:15]:  # Limiter à 15 pour éviter un message trop long
                # Échapper les caractères spéciaux Markdown
                title = sport['title'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
                key = sport['key'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
                message += f"• {title} ({key})\n"
            
            if len(sports) > 15:
                message += f"\n... et {len(sports) - 15} autres sports"
            
            # Ajouter une notification si en mode démo
            if self.demo_mode:
                message += "\n\n⚠️ **Mode Démo** : Sports de démonstration"
            
            await send_message(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sports: {e}")
            await send_message("❌ Erreur lors de la récupération des sports.")
    
    async def matches_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /matches - Tous les matchs à venir (J+0 à J+3)"""
        # Déterminer la méthode d'envoi selon le type d'update
        if update.message:
            send_message = update.message.reply_text
        elif update.callback_query:
            send_message = update.callback_query.message.reply_text
        else:
            logger.error("Update sans message ni callback_query")
            return
        
        await send_message("🔍 Recherche de tous les matchs disponibles (J+0 à J+3)...")
        
        try:
            # Toujours récupérer des données fraîches pour chaque commande
            matches_data = self.sports_api.get_sports_with_matches(days_ahead=3)
            
            if not matches_data:
                await send_message("❌ Aucun match trouvé pour les 3 prochains jours.")
                return
            
            # Compter le total de matchs
            total_matches = sum(len(sport_data['matches']) for sport_data in matches_data.values())
            
            # Message principal avec toutes les informations
            message = f"📅 **MATCHS DISPONIBLES - {total_matches} matchs trouvés**\n"
            message += f"🗓️ Période : J+0 à J+3 (du {datetime.now().strftime('%d/%m')} au {(datetime.now() + timedelta(days=3)).strftime('%d/%m')})\n"
            message += f"🏆 Sports couverts : {len(matches_data)}\n"
            
            # Ajouter une notification si en mode démo
            if self.demo_mode:
                message += "⚠️ **Mode Démo** : Données factices pour démonstration\n"
            
            message += "\n" + "="*40 + "\n\n"
            
            # Afficher TOUS les sports et TOUS les matchs (structure complète)
            for sport_key, sport_data in matches_data.items():
                matches = sport_data['matches']
                sport_emoji = self._get_sport_emoji(sport_key)
                
                message += f"{sport_emoji} **{sport_data['title'].upper()}** ({len(matches)} matchs)\n"
                message += "─" * 25 + "\n"
                
                # Afficher TOUS les matchs de ce sport
                for i, match in enumerate(matches, 1):
                    formatted_match = self.sports_api.format_match_info(match)
                    message += f"{i}. {formatted_match}\n"
                
                message += "\n"
            
            # Boutons pour analyses et combinés
            keyboard = [
                [InlineKeyboardButton("🧠 Analyser TOUS les matchs", callback_data="analyze_all")],
                [InlineKeyboardButton("🎲 Générer combinés SAFE", callback_data="generate_safe")],
                [InlineKeyboardButton("⚖️ Générer combinés MOYEN", callback_data="generate_medium")],
                [InlineKeyboardButton("🚀 Générer combinés HIGH RISK", callback_data="generate_high_risk")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Envoyer un nouveau message propre à chaque fois
            await send_message(message, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des matchs: {e}")
            await send_message("❌ Erreur lors de la récupération des matchs.")
    
    def _get_sport_emoji(self, sport_key: str) -> str:
        """Retourne l'emoji approprié pour un sport"""
        sport_emojis = {
            'soccer': '⚽',
            'americanfootball': '🏈', 
            'basketball': '🏀',
            'baseball': '⚾',
            'icehockey': '🏒',
            'tennis': '🎾',
            'golf': '⛳',
            'boxing': '🥊'
        }
        
        for key, emoji in sport_emojis.items():
            if key in sport_key.lower():
                return emoji
        return '🏆'
    
    async def analysis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /analysis - Analyse complète"""
        # Déterminer la méthode d'envoi selon le type d'update
        if update.message:
            send_message = update.message.reply_text
        elif update.callback_query:
            send_message = update.callback_query.message.reply_text
        else:
            logger.error("Update sans message ni callback_query")
            return
        
        await send_message("🧠 Analyse en cours...")
        
        try:
            # Récupérer les matchs
            cache_key = "all_matches"
            if self._is_cache_valid(cache_key):
                matches_data = self.cache[cache_key]['data']
            else:
                matches_data = self.sports_api.get_sports_with_matches(days_ahead=3)
                self._update_cache(cache_key, matches_data)
            
            if not matches_data:
                await send_message("❌ Aucun match à analyser.")
                return
            
            # Analyser tous les matchs
            all_analyses = []
            for sport_data in matches_data.values():
                for match in sport_data['matches']:
                    analysis = self.betting_analyzer.analyze_match(match)
                    if analysis['confidence'] > 0:
                        all_analyses.append(analysis)
            
            if not all_analyses:
                await send_message("❌ Aucune analyse disponible.")
                return
            
            # Trier par confiance
            all_analyses.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Préparer le message
            message = f"📊 **ANALYSE COMPLÈTE DE {len(all_analyses)} MATCHS**\n\n"
            
            # Statistiques en premier
            high_confidence = len([a for a in all_analyses if a['confidence'] >= 70])
            medium_confidence = len([a for a in all_analyses if 50 <= a['confidence'] < 70])
            low_confidence = len([a for a in all_analyses if a['confidence'] < 50])
            value_bets = len([a for a in all_analyses if a['value_bet']])
            
            message += f"📈 **STATISTIQUES GLOBALES :**\n"
            message += f"• 🟢 {high_confidence} paris haute confiance (≥70%)\n"
            message += f"• 🟡 {medium_confidence} paris moyenne confiance (50-69%)\n"
            message += f"• 🔴 {low_confidence} paris faible confiance (<50%)\n"
            message += f"• 💎 {value_bets} value bets détectées\n\n"
            
            # Envoyer les statistiques d'abord
            await send_message(message, parse_mode='Markdown')
            
            # Diviser les analyses en groupes pour éviter les messages trop longs
            analyses_per_message = 10  # 10 analyses par message maximum
            total_messages = (len(all_analyses) + analyses_per_message - 1) // analyses_per_message
            
            for msg_num in range(total_messages):
                start_idx = msg_num * analyses_per_message
                end_idx = min((msg_num + 1) * analyses_per_message, len(all_analyses))
                
                analyses_chunk = all_analyses[start_idx:end_idx]
                
                chunk_message = f"📋 **ANALYSES {start_idx + 1}-{end_idx} sur {len(all_analyses)} :**\n\n"
                
                for i, analysis in enumerate(analyses_chunk, start_idx + 1):
                    confidence_emoji = "🟢" if analysis['confidence'] >= 70 else "🟡" if analysis['confidence'] >= 50 else "🔴"
                    value_emoji = "💎" if analysis['value_bet'] else ""
                    
                    chunk_message += f"{i}. {confidence_emoji} {analysis['match']}\n"
                    chunk_message += f"   ➤ {analysis['recommendation']}\n"
                    chunk_message += f"   📈 Confiance: {analysis['confidence']}% {value_emoji}\n\n"
                
                await send_message(chunk_message, parse_mode='Markdown')
                await asyncio.sleep(1)  # Délai entre les messages
            
            # Message final avec bouton pour les combinés
            final_message = "✅ **ANALYSE TERMINÉE !**\n\n"
            final_message += f"📊 {len(all_analyses)} matchs analysés au total\n"
            final_message += f"🏆 {high_confidence} paris haute confiance disponibles\n"
            final_message += f"💎 {value_bets} value bets détectées\n\n"
            final_message += "Vous pouvez maintenant générer des combinés :"
            
            # Bouton pour les combinés
            keyboard = [[InlineKeyboardButton("🎲 Générer des combinés", callback_data="generate_combos")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await send_message(final_message, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            await send_message("❌ Erreur lors de l'analyse.")
    
    async def combos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /combos - Génération de tous les types de combinés"""
        await self._generate_all_combinations(update, context)
    
    async def _generate_combinations_by_level(self, update: Update, context: ContextTypes.DEFAULT_TYPE, level: str):
        """Génère des combinés d'un niveau spécifique"""
        send_message = update.message.reply_text if update.message else update.callback_query.message.reply_text
        
        level_info = {
            "SAFE": {
                "emoji": "🛡️",
                "name": "SAFE",
                "description": "Combinés sûrs - Petites cotes, très forte probabilité",
                "min_confidence": 75,
                "max_odds": 2.5
            },
            "MOYEN": {
                "emoji": "⚖️", 
                "name": "MOYEN",
                "description": "Combinés équilibrés - Cotes moyennes, bon potentiel",
                "min_confidence": 60,
                "max_odds": 4.0
            },
            "HIGH_RISK": {
                "emoji": "🚀",
                "name": "HIGH RISK / HIGH REWARD", 
                "description": "Combinés risqués - Grosses cotes, gros potentiel",
                "min_confidence": 45,
                "max_odds": 10.0
            }
        }
        
        level_config = level_info[level]
        
        await send_message(f"{level_config['emoji']} Génération de combinés {level_config['name']}...")
        
        try:
            # Récupérer et analyser les matchs
            matches_data = self.sports_api.get_sports_with_matches(days_ahead=3)
            
            if not matches_data:
                await send_message("❌ Aucun match disponible pour les combinés.")
                return
            
            # Analyser tous les matchs
            all_analyses = []
            for sport_data in matches_data.values():
                for match in sport_data['matches']:
                    analysis = self.betting_analyzer.analyze_match(match)
                    if analysis['confidence'] >= level_config['min_confidence']:
                        # Extraire les cotes pour filtrer
                        try:
                            odds_str = analysis['recommendation'].split('(cote: ')[1].split(')')[0]
                            odds = float(odds_str)
                            if odds <= level_config['max_odds']:
                                all_analyses.append(analysis)
                        except:
                            # Si on ne peut pas extraire les cotes, on garde quand même
                            all_analyses.append(analysis)
            
            if len(all_analyses) < 3:
                await send_message(f"❌ Pas assez de paris {level_config['name']} fiables (minimum 3 requis, {len(all_analyses)} trouvés).")
                return
            
            # Générer le combiné spécifique
            combination = self.betting_analyzer.generate_specific_combination(all_analyses, level)
            
            if not combination:
                await send_message(f"❌ Impossible de générer un combiné {level_config['name']}.")
                return
            
            # Formatter et envoyer le combiné
            combo_message = f"{level_config['emoji']} **COMBINÉ {level_config['name']}**\n\n"
            combo_message += f"📋 {level_config['description']}\n\n"
            combo_message += self.betting_analyzer.format_combination(combination)
            
            await send_message(combo_message, parse_mode='Markdown')
            
            # Message de conseils spécifique au niveau
            if level == "SAFE":
                advice = "💡 **Conseil SAFE :** Combiné à faible risque, idéal pour préserver votre bankroll."
            elif level == "MOYEN":
                advice = "💡 **Conseil MOYEN :** Bon équilibre risque/rendement, gérez votre mise prudemment."
            else:
                advice = "💡 **Conseil HIGH RISK :** Mise très réduite recommandée ! Potentiel élevé mais risque maximal."
            
            await send_message(advice, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du combiné {level}: {e}")
            await send_message(f"❌ Erreur lors de la génération du combiné {level_config['name']}.")
    
    async def _generate_all_combinations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Génère et affiche tous les types de combinés"""
        send_message = update.message.reply_text if update.message else update.callback_query.message.reply_text
        
        await send_message("🎲 Génération de TOUS les types de combinés...")
        
        # Générer chaque niveau
        for level in ["SAFE", "MOYEN", "HIGH_RISK"]:
            await self._generate_combinations_by_level(update, context, level)
            await asyncio.sleep(2)  # Délai entre les combinés
        
        # Message final
        final_message = f"""
🎯 **TOUS LES COMBINÉS GÉNÉRÉS !**

💡 **Conseils généraux :**
• 🛡️ SAFE : Mise standard (ex: 10€)
• ⚖️ MOYEN : Mise réduite (ex: 5€) 
• 🚀 HIGH RISK : Mise minimale (ex: 1-2€)

⚠️ **Règles d'or :**
• Ne jamais miser plus que vous ne pouvez perdre
• Diversifiez vos mises selon les niveaux
• Les cotes peuvent changer rapidement

🔄 Utilisez `/matches` pour voir les nouveaux matchs
        """
        await send_message(final_message, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestion des boutons inline"""
        query = update.callback_query
        await query.answer()
        
        # Boutons des commandes principales (depuis /start)
        if query.data == "cmd_matches":
            await self.matches_command(update, context)
        elif query.data == "cmd_analysis":
            await self.analysis_command(update, context)
        elif query.data == "cmd_combos":
            await self.combos_command(update, context)
        elif query.data == "cmd_sports":
            await self.sports_command(update, context)
        elif query.data == "cmd_help":
            await self.help_command(update, context)
        
        # Boutons d'analyse et combinés (depuis /matches)
        elif query.data == "analyze_all":
            await self.analysis_command(update, context)
        elif query.data == "generate_safe":
            await self._generate_combinations_by_level(update, context, "SAFE")
        elif query.data == "generate_medium":
            await self._generate_combinations_by_level(update, context, "MOYEN")
        elif query.data == "generate_high_risk":
            await self._generate_combinations_by_level(update, context, "HIGH_RISK")
        elif query.data == "generate_combos":
            # Ancien système - générer tous les types
            await self._generate_all_combinations(update, context)
    
    async def _generate_combinations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Génère et affiche les combinés"""
        # Utiliser message.reply_text si c'est une commande, sinon edit_message_text pour les callbacks
        send_message = update.message.reply_text if update.message else update.callback_query.edit_message_text
        
        await send_message("🎲 Génération des combinés...")
        
        try:
            # Récupérer et analyser les matchs
            matches_data = self.sports_api.get_sports_with_matches(days_ahead=3)
            
            if not matches_data:
                await send_message("❌ Aucun match disponible pour les combinés.")
                return
            
            # Analyser tous les matchs
            all_analyses = []
            for sport_data in matches_data.values():
                for match in sport_data['matches']:
                    analysis = self.betting_analyzer.analyze_match(match)
                    if analysis['confidence'] >= 50:  # Seulement les paris fiables
                        all_analyses.append(analysis)
            
            if len(all_analyses) < 3:
                await send_message("❌ Pas assez de paris fiables pour générer des combinés.")
                return
            
            # Générer les combinés
            combinations = self.betting_analyzer.generate_combinations(all_analyses, combo_size=3)
            
            if not combinations:
                await send_message("❌ Impossible de générer des combinés.")
                return
            
            # Afficher chaque combiné
            for combination in combinations:
                combo_message = self.betting_analyzer.format_combination(combination)
                await send_message(combo_message, parse_mode='Markdown')
                await asyncio.sleep(1)  # Petit délai entre les messages
            
            # Message de fin
            final_message = f"""
💡 **Conseils :**
• Gérez votre bankroll prudemment
• Ne misez jamais plus que vous ne pouvez perdre
• Les cotes peuvent changer rapidement
• Vérifiez toujours avant de parier

🔄 Utilisez `/matches` pour voir les nouveaux matchs
            """
            await send_message(final_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des combinés: {e}")
            await send_message("❌ Erreur lors de la génération des combinés.")
    
    def _is_cache_valid(self, key: str) -> bool:
        """Vérifie si le cache est encore valide"""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]['timestamp']
        current_time = datetime.now().timestamp()
        
        return (current_time - cache_time) < self.cache_timeout
    
    def _update_cache(self, key: str, data):
        """Met à jour le cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    async def pre_process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pré-traitement pour détecter les nouveaux utilisateurs"""
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        
        # Si c'est un nouvel utilisateur, on l'enregistre et on déclenche /start
        if self._is_new_user(user_id):
            logger.info(f"Premier contact avec l'utilisateur {user_id} ({update.effective_user.first_name})")
            
            # Enregistrer l'utilisateur
            self._register_user(user_id)
            
            # Déclencher automatiquement /start
            await self.start_command(update, context)
            
            # Marquer le message comme traité pour éviter qu'il passe aux autres handlers
            context.drop_callback_data = True
            return
    
    async def handle_any_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestionnaire pour les messages non-commandes d'utilisateurs connus"""
        # Vérifier que c'est bien un utilisateur connu pour éviter les doublons
        if (update.effective_user and 
            not self._is_new_user(update.effective_user.id) and
            update.message and 
            update.message.text and 
            not update.message.text.startswith('/')):
            
            suggestion_message = """
❓ Je ne comprends pas ce message. Voici ce que je peux faire :

🔍 `/matches` - Voir tous les matchs à venir
📊 `/analysis` - Analyse complète des matchs
🎲 `/combos` - Générer des combinés
⚽ `/sports` - Sports disponibles
❓ `/help` - Aide détaillée

Tapez une commande pour commencer !
            """
            await update.message.reply_text(suggestion_message)

    def run(self):
        """Lance BetIQ 2.5"""
        logger.info("Démarrage de BetIQ 2.5...")
        
        # Créer l'application
        application = Application.builder().token(self.telegram_token).build()
        
        # Ajouter les handlers dans l'ordre de priorité
        # Handler de pré-traitement pour nouveaux utilisateurs (groupe -1 = priorité max)
        application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VOICE, self.pre_process_message), group=-1)
        
        # Puis les commandes spécifiques
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("sports", self.sports_command))
        application.add_handler(CommandHandler("matches", self.matches_command))
        application.add_handler(CommandHandler("analysis", self.analysis_command))
        application.add_handler(CommandHandler("combos", self.combos_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Enfin le handler pour les messages non-commandes
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_any_message), group=1)
        
        # Démarrer le bot
        logger.info("BetIQ 2.5 démarré ! Utilisez Ctrl+C pour arrêter.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Point d'entrée principal"""
    import sys
    
    # Vérifier si le mode démo est demandé
    demo_mode = "--demo" in sys.argv or "-d" in sys.argv
    
    if demo_mode:
        print("🎭 BetIQ 2.5 - Démarrage en mode DÉMO")
        print("📊 Utilisation de données factices pour la démonstration")
        print("⚠️  Les matchs et cotes affichés ne sont pas réels")
        print("-" * 50)
    
    try:
        bot = BetIQ25Bot(demo_mode=demo_mode)
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")

if __name__ == "__main__":
    main()
