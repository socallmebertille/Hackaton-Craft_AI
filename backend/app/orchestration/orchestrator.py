"""
Orchestrateur principal pour l'IA Juridique

Gère le flux de traitement des messages utilisateur :
1. Analyse l'intention via Pipeline 0
2. Route vers le bon pipeline selon l'intention
3. Retourne la réponse appropriée
"""

import httpx
from typing import Dict, Any, Optional
from app.core.config import settings


class AIOrchestrator:
    """Orchestrateur pour coordonner les pipelines CraftAI"""

    def __init__(self):
        """Initialise l'orchestrateur avec les configurations des pipelines"""
        self.pipeline_0_url = settings.PIPELINE_0_ENDPOINT_URL
        self.pipeline_0_token = settings.PIPELINE_0_ENDPOINT_TOKEN

        # Pipeline 1 : Extraction Légifrance (pour DEBAT et CITATIONS)
        self.pipeline_1_url = settings.PIPELINE_1_ENDPOINT_URL
        self.pipeline_1_token = settings.PIPELINE_1_ENDPOINT_TOKEN

    async def process_message(self, message: str, user_id: int, chat_id: int) -> Dict[str, Any]:
        """
        Traite un message utilisateur à travers les pipelines

        Args:
            message: Message de l'utilisateur
            user_id: ID de l'utilisateur
            chat_id: ID du chat

        Returns:
            dict: Réponse avec l'intention et le contenu approprié
        """
        print(f"[Orchestrateur] Traitement du message: {message[:100]}...")

        # Étape 1: Analyser l'intention (Pipeline 0)
        intention_result = await self._call_pipeline_0(message)

        if not intention_result:
            return {
                "success": False,
                "error": "Erreur lors de l'analyse de l'intention",
                "message": "Désolé, une erreur s'est produite lors de l'analyse de votre message."
            }

        # intention_result est déjà le dict avec {message, intention, confidence, reasoning}
        intention_data = intention_result
        intention = intention_data.get("intention")
        confidence = intention_data.get("confidence", 0)

        print(f"[Orchestrateur] Intention détectée: {intention} (confiance: {confidence})")

        # Étape 2: Gérer selon l'intention
        if intention == "HORS_SUJET":
            return await self._handle_hors_sujet(message, intention_data)

        elif intention == "DEBAT":
            return await self._handle_debat(message, user_id, chat_id, intention_data)

        elif intention == "CITATIONS":
            return await self._handle_citations(message, user_id, chat_id, intention_data)

        else:
            # Intention inconnue - traiter comme hors sujet par sécurité
            return await self._handle_hors_sujet(message, intention_data)

    async def _call_pipeline_0(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Appelle le Pipeline 0 (analyse d'intention)

        Args:
            message: Message à analyser

        Returns:
            dict: Résultat de l'analyse ou None si erreur
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.post(
                    self.pipeline_0_url,
                    headers={
                        "Authorization": f"EndpointToken {self.pipeline_0_token}",
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    json={"message": message}
                )

                response.raise_for_status()
                data = response.json()

                # Vérifier le statut
                if data.get("status") != "Succeeded":
                    print(f"[Orchestrateur] Pipeline 0 failed: {data}")
                    return None

                return data.get("outputs", {}).get("result", {}).get("value")

        except httpx.HTTPError as e:
            print(f"[Orchestrateur] Erreur HTTP lors de l'appel au Pipeline 0: {e}")
            return None
        except Exception as e:
            print(f"[Orchestrateur] Erreur lors de l'appel au Pipeline 0: {e}")
            return None

    async def _call_pipeline_1(self, message: str, intention: str) -> Optional[Dict[str, Any]]:
        """
        Appelle le Pipeline 1 (extraction Légifrance)

        Args:
            message: Message de l'utilisateur
            intention: Type d'intention (DEBAT ou CITATIONS)

        Returns:
            dict: Résultat de l'extraction ou None si erreur
        """
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.post(
                    self.pipeline_1_url,
                    headers={
                        "Authorization": f"EndpointToken {self.pipeline_1_token}",
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    json={
                        "message": message,
                        "intention": intention
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Vérifier le statut
                if data.get("status") != "Succeeded":
                    print(f"[Orchestrateur] Pipeline 1 failed: {data}")
                    return None

                return data.get("outputs", {}).get("result", {}).get("value")

        except httpx.HTTPError as e:
            print(f"[Orchestrateur] Erreur HTTP lors de l'appel au Pipeline 1: {e}")
            return None
        except Exception as e:
            print(f"[Orchestrateur] Erreur lors de l'appel au Pipeline 1: {e}")
            return None

    async def _handle_hors_sujet(self, message: str, intention_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les messages hors sujet

        Args:
            message: Message de l'utilisateur
            intention_data: Données d'intention du Pipeline 0

        Returns:
            dict: Réponse pour hors sujet
        """
        print(f"[Orchestrateur] Message hors sujet détecté - Fin de la discussion")

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

    async def _handle_debat(
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
            dict: Réponse avec analyse juridique
        """
        print(f"[Orchestrateur] Traitement d'une demande de débat juridique")

        # Appeler Pipeline 1 (Extraction Légifrance)
        legifrance_result = await self._call_pipeline_1(message, "DEBAT")

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

        # Formater la réponse pour l'utilisateur
        response_text = self._format_debat_response(legifrance_result)

        return {
            "success": True,
            "intention": "DEBAT",
            "confidence": intention_data.get("confidence", 0),
            "response": response_text,
            "sources": {
                "codes": legifrance_result.get("codes", []),
                "jurisprudence": legifrance_result.get("jurisprudence", []),
                "search_strategy": legifrance_result.get("search_strategy", ""),
                "keywords_used": legifrance_result.get("keywords_used", [])
            },
            "end_conversation": False
        }

    async def _handle_citations(
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
        print(f"[Orchestrateur] Traitement d'une demande de citations légales")

        # Appeler Pipeline 1 (Extraction Légifrance)
        legifrance_result = await self._call_pipeline_1(message, "CITATIONS")

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

        # Formater la réponse pour l'utilisateur
        response_text = self._format_citations_response(legifrance_result)

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
            "end_conversation": False
        }

    def _format_debat_response(self, legifrance_result: Dict[str, Any]) -> str:
        """
        Formate la réponse pour une demande de débat

        Args:
            legifrance_result: Résultats du Pipeline 1

        Returns:
            str: Texte formaté pour l'utilisateur
        """
        codes = legifrance_result.get("codes", [])
        jurisprudence = legifrance_result.get("jurisprudence", [])

        response_parts = []

        # Introduction
        response_parts.append(
            f"J'ai trouvé {len(codes)} article(s) de code et {len(jurisprudence)} jurisprudence(s) "
            "pertinents pour votre question.\n"
        )

        # Articles de code
        if codes:
            response_parts.append("\n📖 **Articles de Code**\n")
            for i, code in enumerate(codes[:3], 1):  # Limiter à 3 pour la lisibilité
                article_num = code.get("article_num", "N/A")
                code_title = code.get("code_title", "Code").replace("<mark>", "").replace("</mark>", "")
                text = code.get("text_preview", "").replace("<mark>", "**").replace("</mark>", "**")

                # Nettoyer le texte
                text = text.replace("[...]", "").strip()
                if len(text) > 300:
                    text = text[:300] + "..."

                response_parts.append(f"{i}. **{code_title} - Article {article_num}**")
                response_parts.append(f"   {text}\n")

        # Jurisprudence
        if jurisprudence:
            response_parts.append("\n⚖️ **Jurisprudence Pertinente**\n")
            for i, juris in enumerate(jurisprudence[:3], 1):  # Limiter à 3
                title = juris.get("title", "").replace("<mark>", "**").replace("</mark>", "**")
                text = juris.get("text_preview", "").replace("<mark>", "**").replace("</mark>", "**")

                # Nettoyer et raccourcir
                text = text.replace("[...]", "").strip()
                if len(text) > 200:
                    text = text[:200] + "..."

                response_parts.append(f"{i}. {title}")
                if text:
                    response_parts.append(f"   {text}\n")

        # Stratégie de recherche
        search_strategy = legifrance_result.get("search_strategy", "")
        keywords = legifrance_result.get("keywords_used", [])

        if keywords:
            response_parts.append(f"\n🔍 Mots-clés utilisés : {', '.join(keywords)}")

        return "\n".join(response_parts)

    def _format_citations_response(self, legifrance_result: Dict[str, Any]) -> str:
        """
        Formate la réponse pour une demande de citations

        Args:
            legifrance_result: Résultats du Pipeline 1

        Returns:
            str: Texte formaté avec citations
        """
        codes = legifrance_result.get("codes", [])
        jurisprudence = legifrance_result.get("jurisprudence", [])

        response_parts = []

        # Articles de code (tous)
        if codes:
            response_parts.append("📖 **CODES ET LOIS**\n")
            for code in codes:
                article_num = code.get("article_num", "N/A")
                code_title = code.get("code_title", "Code").replace("<mark>", "").replace("</mark>", "")
                article_id = code.get("article_id", "")
                text = code.get("text_preview", "").replace("<mark>", "").replace("</mark>", "")
                legal_status = code.get("legal_status", "")

                # Nettoyer le texte
                text = text.replace("[...]", "").strip()

                response_parts.append(f"• **{code_title} - Article {article_num}**")
                if legal_status:
                    response_parts.append(f"  Statut : {legal_status}")
                response_parts.append(f"  {text}")
                if article_id:
                    response_parts.append(f"  Référence : {article_id}")
                response_parts.append("")

        # Jurisprudence (toutes)
        if jurisprudence:
            response_parts.append("\n⚖️ **JURISPRUDENCE**\n")
            for juris in jurisprudence:
                title = juris.get("title", "").replace("<mark>", "").replace("</mark>", "")
                text = juris.get("text_preview", "").replace("<mark>", "").replace("</mark>", "")

                # Nettoyer
                text = text.replace("[...]", "").strip()

                response_parts.append(f"• {title}")
                if text:
                    response_parts.append(f"  {text}")
                response_parts.append("")

        # Résumé
        total_codes = legifrance_result.get("total_codes", 0)
        total_jurisprudence = legifrance_result.get("total_jurisprudence", 0)

        response_parts.append(f"\n📊 **Total** : {total_codes} article(s) de code, {total_jurisprudence} jurisprudence(s)")

        return "\n".join(response_parts)
