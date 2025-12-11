"""
Orchestrateur principal pour l'IA Juridique

Gère le flux de traitement des messages utilisateur :
1. Analyse l'intention via Pipeline 0
2. Route vers le bon pipeline selon l'intention
3. Retourne la réponse appropriée
"""

from typing import Dict, Any, Optional
from app.chat.pipeline_client import PipelineClient
from app.chat.data_formatter import DataFormatter
from app.chat.intent_handlers import IntentHandlers


class AIOrchestrator:
    """Orchestrateur pour coordonner les pipelines CraftAI"""

    def __init__(self):
        """Initialise l'orchestrateur avec les composants nécessaires"""
        self.pipeline_client = PipelineClient()
        self.formatter = DataFormatter()
        self.handlers = IntentHandlers(self.pipeline_client, self.formatter)

    async def process_message(
        self,
        message: str,
        user_id: int,
        chat_id: int,
        is_first_message: bool = True,
        chat_history: Optional[list] = None,
        accumulated_legal_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur à travers les pipelines

        Args:
            message: Message de l'utilisateur
            user_id: ID de l'utilisateur
            chat_id: ID du chat
            is_first_message: Si c'est le premier message du chat
            chat_history: Historique des messages (non utilisé)
            accumulated_legal_data: Sources juridiques accumulées (non utilisé)

        Returns:
            dict: Réponse avec l'intention et le contenu approprié
        """
        print(f"[Orchestrateur] Traitement du message: {message[:100]}...")

        # Étape 1: Analyser l'intention (Pipeline 0)
        intention_result = await self.pipeline_client.call_pipeline_0(message)

        if not intention_result:
            return {
                "success": False,
                "error": "Erreur lors de l'analyse de l'intention",
                "message": "Désolé, une erreur s'est produite lors de l'analyse de votre message."
            }

        # Extraire les données d'intention
        intention_data = intention_result
        intention = intention_data.get("intention")
        confidence = intention_data.get("confidence", 0)

        print(f"[Orchestrateur] Intention détectée: {intention} (confiance: {confidence})")

        # Étape 2: Router vers le bon gestionnaire d'intention
        if intention == "HORS_SUJET":
            return await self.handlers.handle_hors_sujet(message, intention_data)

        elif intention == "DEBAT":
            return await self.handlers.handle_debat(message, user_id, chat_id, intention_data)

        elif intention == "CITATIONS":
            return await self.handlers.handle_citations(message, user_id, chat_id, intention_data)

        else:
            # Intention inconnue - traiter comme hors sujet par sécurité
            return await self.handlers.handle_hors_sujet(message, intention_data)
