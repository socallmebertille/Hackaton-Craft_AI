"""
Gestionnaires d'intentions pour l'orchestrateur

Gère la logique métier pour chaque type d'intention :
- HORS_SUJET: Messages non juridiques
- DEBAT: Demandes de débat contradictoire
- CITATIONS: Demandes de citations légales
"""

from typing import Dict, Any
from app.chat.pipeline_client import PipelineClient
from app.chat.data_formatter import DataFormatter


class IntentHandlers:
    """Gestionnaires pour les différents types d'intentions"""

    def __init__(self, pipeline_client: PipelineClient, formatter: DataFormatter):
        """
        Initialise les gestionnaires

        Args:
            pipeline_client: Client pour appeler les pipelines
            formatter: Formateur de données
        """
        self.pipeline_client = pipeline_client
        self.formatter = formatter

    async def handle_hors_sujet(self, message: str, intention_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages hors sujet

        Args:
            message: Message de l'utilisateur
            intention_data: Données d'intention du Pipeline 0

        Returns:
            dict: Réponse pour hors sujet
        """
        print(f"[IntentHandlers] Message hors sujet détecté - Fin de la discussion")

        return {
            "success": True,
            "intention": "HORS_SUJET",
            "confidence": intention_data.get("confidence", 0),
            "reasoning": intention_data.get("reasoning", ""),
            "response": (
                "Je suis un assistant juridique spécialisé en droit français. "
                "Votre question ne semble pas liée au domaine juridique. "
                "Je ne peux malheureusement pas vous aider sur ce sujet.\n\n"
                "N'hésitez pas à me poser des questions concernant le droit, "
                "les lois, ou des conseils juridiques."
            ),
            "end_conversation": True
        }

    async def handle_debat(
        self,
        message: str,
        user_id: int,
        chat_id: int,
        intention_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gère les demandes de débat/discussion juridique

        Args:
            message: Message de l'utilisateur
            user_id: ID de l'utilisateur
            chat_id: ID du chat
            intention_data: Données d'intention du Pipeline 0

        Returns:
            dict: Réponse avec débat contradictoire
        """
        print(f"[IntentHandlers] Traitement d'une demande de débat juridique")

        # Étape 1: Appeler Pipeline 1 (Extraction Légifrance)
        legifrance_result = await self.pipeline_client.call_pipeline_1(message, "DEBAT")

        if not legifrance_result:
            return {
                "success": True,
                "intention": "DEBAT",
                "confidence": intention_data.get("confidence", 0),
                "response": (
                    "Désolé, je n'ai pas pu récupérer les informations juridiques nécessaires. "
                    "Veuillez réessayer."
                ),
                "end_conversation": False
            }

        # Étape 2: Nettoyer les données pour P3
        cleaned_legal_data = self.formatter.clean_legal_data(legifrance_result)

        # Étape 3: Appeler Pipeline 3 (Débat)
        debate_result = await self.pipeline_client.call_pipeline_3(message, cleaned_legal_data)

        if not debate_result:
            return {
                "success": False,
                "intention": "DEBAT",
                "confidence": intention_data.get("confidence", 0),
                "error": "Le Pipeline 3 (débat juridique) a échoué",
                "response": "Désolé, une erreur s'est produite lors de la génération du débat juridique. Veuillez réessayer.",
                "end_conversation": False
            }

        # Structurer le débat en plusieurs messages
        debate_messages = self.formatter.structure_debate_messages(debate_result)

        return {
            "success": True,
            "intention": "DEBAT",
            "confidence": intention_data.get("confidence", 0),
            "debate_messages": debate_messages,  # Liste de messages structurés
            "debate": debate_result,
            "legal_data": cleaned_legal_data,
            "end_conversation": False
        }

    async def handle_citations(
        self,
        message: str,
        user_id: int,
        chat_id: int,
        intention_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gère les demandes de citations de lois/jurisprudence

        Args:
            message: Message de l'utilisateur
            user_id: ID de l'utilisateur
            chat_id: ID du chat
            intention_data: Données d'intention du Pipeline 0

        Returns:
            dict: Réponse avec citations légales
        """
        print(f"[IntentHandlers] Traitement d'une demande de citations légales")

        # Étape 1: Appeler Pipeline 1 (Extraction Légifrance)
        legifrance_result = await self.pipeline_client.call_pipeline_1(message, "CITATIONS")

        if not legifrance_result:
            return {
                "success": True,
                "intention": "CITATIONS",
                "confidence": intention_data.get("confidence", 0),
                "response": (
                    "Désolé, je n'ai pas pu récupérer les citations juridiques. "
                    "Veuillez réessayer."
                ),
                "end_conversation": False
            }

        # Étape 2: Nettoyer les données pour P4
        cleaned_legal_data = self.formatter.clean_legal_data(legifrance_result)

        # Étape 3: Appeler Pipeline 4 (Citations avec explications)
        citation_result = await self.pipeline_client.call_pipeline_4(message, cleaned_legal_data)

        if not citation_result:
            return {
                "success": False,
                "intention": "CITATIONS",
                "confidence": intention_data.get("confidence", 0),
                "error": "Le Pipeline 4 (citations) a échoué",
                "response": "Désolé, une erreur s'est produite lors de la génération des citations. Veuillez réessayer.",
                "end_conversation": False
            }

        # Formater la réponse avec les explications du Pipeline 4
        response_text = self.formatter.format_citation_result(citation_result)

        return {
            "success": True,
            "intention": "CITATIONS",
            "confidence": intention_data.get("confidence", 0),
            "response": response_text,
            "citations": {
                "codes": legifrance_result.get("codes", []),
                "jurisprudence": legifrance_result.get("jurisprudence", []),
                "total_codes": legifrance_result.get("total_codes", 0),
                "total_jurisprudence": legifrance_result.get("total_jurisprudence", 0)
            },
            "legal_data": cleaned_legal_data,  # Sources utilisées pour accumuler
            "end_conversation": False
        }
