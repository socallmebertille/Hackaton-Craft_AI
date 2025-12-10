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

        # Pipeline 3 : Débat juridique
        self.pipeline_3_url = settings.PIPELINE_3_ENDPOINT_URL
        self.pipeline_3_token = settings.PIPELINE_3_ENDPOINT_TOKEN

        # Pipeline 4 : Citations avec explications
        self.pipeline_4_url = settings.PIPELINE_4_ENDPOINT_URL
        self.pipeline_4_token = settings.PIPELINE_4_ENDPOINT_TOKEN

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

    def _clean_legal_data_for_p3(self, legal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie les données juridiques pour P3 en supprimant les champs vides ou None

        Args:
            legal_data: Données brutes de P1

        Returns:
            dict: Données nettoyées
        """
        cleaned = {
            "codes": [],
            "jurisprudence": [],
            "total_codes": legal_data.get("total_codes", 0),
            "total_jurisprudence": legal_data.get("total_jurisprudence", 0)
        }

        # Nettoyer les codes
        for code in legal_data.get("codes", []):
            cleaned_code = {
                "type": code.get("type", "CODE"),
                "code_title": code.get("code_title", ""),
                "article_num": code.get("article_num", ""),
                "article_id": code.get("article_id", ""),
                "text_preview": code.get("text_preview", ""),
                "legal_status": code.get("legal_status", "")
            }
            # Supprimer les champs vides pour réduire la taille
            cleaned_code = {k: v for k, v in cleaned_code.items() if v}
            cleaned["codes"].append(cleaned_code)

        # Nettoyer la jurisprudence - IMPORTANT: supprimer les champs None/vides
        for juris in legal_data.get("jurisprudence", []):
            cleaned_juris = {
                "type": juris.get("type", "JURISPRUDENCE"),
                "title": juris.get("title", ""),
                "text_preview": juris.get("text_preview", "")
            }
            # Ajouter decision_id et date seulement s'ils existent et ne sont pas vides
            if juris.get("decision_id"):
                cleaned_juris["decision_id"] = juris["decision_id"]
            if juris.get("date"):
                cleaned_juris["date"] = juris["date"]
            if juris.get("juridiction"):
                cleaned_juris["juridiction"] = juris["juridiction"]

            # Supprimer les champs vides
            cleaned_juris = {k: v for k, v in cleaned_juris.items() if v}
            cleaned["jurisprudence"].append(cleaned_juris)

        return cleaned

    async def _call_pipeline_3(self, message: str, legal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Appelle le Pipeline 3 (débat juridique)

        Args:
            message: Message de l'utilisateur
            legal_data: Données juridiques de P1

        Returns:
            dict: Résultat du débat ou None si erreur
        """
        try:
            print(f"[Orchestrateur] Appel Pipeline 3 avec {legal_data.get('total_codes', 0)} codes et {legal_data.get('total_jurisprudence', 0)} jurisprudences")

            async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
                payload = {
                    "message": message,
                    "legal_data": legal_data
                }

                response = await client.post(
                    self.pipeline_3_url,
                    headers={
                        "Authorization": f"EndpointToken {self.pipeline_3_token}",
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                # Vérifier le statut
                if data.get("status") != "Succeeded":
                    print(f"[Orchestrateur] Pipeline 3 failed: {data}")
                    return None

                result = data.get("outputs", {}).get("result", {}).get("value")

                if result:
                    print(f"[Orchestrateur] Pipeline 3 succeeded - Position POUR: {result.get('position_pour', '')[:50]}...")
                else:
                    print(f"[Orchestrateur] Pipeline 3 returned null result")

                return result

        except httpx.HTTPError as e:
            print(f"[Orchestrateur] Erreur HTTP lors de l'appel au Pipeline 3: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[Orchestrateur] Response body: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"[Orchestrateur] Erreur lors de l'appel au Pipeline 3: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _call_pipeline_4(self, message: str, legal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Appelle le Pipeline 4 (citations avec explications)

        Args:
            message: Message de l'utilisateur
            legal_data: Données juridiques de P1

        Returns:
            dict: Résultat des citations ou None si erreur
        """
        try:
            if not self.pipeline_4_url or not self.pipeline_4_token:
                print("[Orchestrateur] Pipeline 4 non configuré")
                return None

            print(f"[Orchestrateur] Appel Pipeline 4 avec {legal_data.get('total_codes', 0)} codes et {legal_data.get('total_jurisprudence', 0)} jurisprudences")

            # Loguer un échantillon des données pour debug
            import json
            if legal_data.get('jurisprudence'):
                print(f"[Orchestrateur] Échantillon jurisprudence[0]: {json.dumps(legal_data['jurisprudence'][0], indent=2, default=str)[:300]}...")

            async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
                payload = {
                    "message": message,
                    "legal_data": legal_data
                }

                response = await client.post(
                    self.pipeline_4_url,
                    headers={
                        "Authorization": f"EndpointToken {self.pipeline_4_token}",
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                # Vérifier le statut
                if data.get("status") != "Succeeded":
                    print(f"[Orchestrateur] Pipeline 4 failed: {data}")
                    return None

                result = data.get("outputs", {}).get("result", {}).get("value")

                if result:
                    print(f"[Orchestrateur] Pipeline 4 succeeded - {len(result.get('codes_expliques', []))} codes expliqués")
                else:
                    print(f"[Orchestrateur] Pipeline 4 returned null result")

                return result

        except httpx.HTTPError as e:
            print(f"[Orchestrateur] Erreur HTTP lors de l'appel au Pipeline 4: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[Orchestrateur] Response body: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"[Orchestrateur] Erreur lors de l'appel au Pipeline 4: {e}")
            import traceback
            traceback.print_exc()
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
            dict: Réponse avec débat contradictoire
        """
        print(f"[Orchestrateur] Traitement d'une demande de débat juridique")

        # Étape 1: Appeler Pipeline 1 (Extraction Légifrance)
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

        # Étape 2: Nettoyer les données pour P3
        cleaned_legal_data = self._clean_legal_data_for_p3(legifrance_result)

        # Étape 3: Appeler Pipeline 3 (Débat)
        debate_result = await self._call_pipeline_3(message, cleaned_legal_data)

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
        debate_messages = self._structure_debate_messages(debate_result)

        return {
            "success": True,
            "intention": "DEBAT",
            "confidence": intention_data.get("confidence", 0),
            "debate_messages": debate_messages,  # Liste de messages structurés
            "debate": debate_result,
            "legal_data": cleaned_legal_data,
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

        # Étape 1: Appeler Pipeline 1 (Extraction Légifrance)
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

        # Étape 2: Nettoyer les données pour P4
        cleaned_legal_data = self._clean_legal_data_for_p3(legifrance_result)

        # Étape 3: Appeler Pipeline 4 (Citations avec explications)
        citation_result = await self._call_pipeline_4(message, cleaned_legal_data)

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
        response_text = self._format_citation_result(citation_result)

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

    def _structure_debate_messages(self, debate_result: Dict[str, Any]) -> list:
        """
        Structure le débat en plusieurs messages séparés

        Args:
            debate_result: Résultat du Pipeline 3

        Returns:
            list: Liste de messages structurés
        """
        messages = []

        def ensure_string(value):
            """Convertit n'importe quelle valeur en string"""
            if isinstance(value, str):
                return value
            elif isinstance(value, list):
                return " ".join([ensure_string(v) for v in value])
            else:
                return str(value)

        # Message 1: Positions du débat
        position_pour = debate_result.get("position_pour", "")
        position_contre = debate_result.get("position_contre", "")
        if position_pour or position_contre:
            positions_text = "## Positions du débat\n"
            if position_pour:
                positions_text += f"**POUR** : {ensure_string(position_pour)}\n\n"
            if position_contre:
                positions_text += f"**CONTRE** : {ensure_string(position_contre)}"
            messages.append(positions_text)

        # Message 2: Arguments POUR Round 1
        pour_r1 = debate_result.get("pour_round_1", "")
        if pour_r1:
            messages.append(f"## Arguments POUR\n{ensure_string(pour_r1)}")

        # Message 3: Arguments CONTRE Round 1
        contre_r1 = debate_result.get("contre_round_1", "")
        if contre_r1:
            messages.append(f"## Arguments CONTRE\n{ensure_string(contre_r1)}")

        # Message 4: Réfutation POUR Round 2
        pour_r2 = debate_result.get("pour_round_2", "")
        if pour_r2:
            messages.append(f"## Réfutation et renforcement POUR\n{ensure_string(pour_r2)}")

        # Message 5: Réfutation CONTRE Round 2
        contre_r2 = debate_result.get("contre_round_2", "")
        if contre_r2:
            messages.append(f"## Réfutation et renforcement CONTRE\n{ensure_string(contre_r2)}")

        # Message 6: Synthèse
        synthese = debate_result.get("synthese", "")
        if synthese:
            messages.append(f"## Synthèse\n{ensure_string(synthese)}")

        # Message 7: Sources citées
        sources = debate_result.get("sources_citees", [])
        if sources:
            sources_str = []
            for s in sources:
                if isinstance(s, str):
                    sources_str.append(s)
                elif isinstance(s, list):
                    sources_str.extend([str(x) for x in s])
                else:
                    sources_str.append(str(s))

            sources_text = "## Sources juridiques citées\n"
            # Une source par ligne avec bullet point
            for source in sources_str:
                sources_text += f"• {source}\n"
            messages.append(sources_text)

        return messages

    def _format_debate_result(self, debate_result: Dict[str, Any]) -> str:
        """
        Formate le résultat du débat pour l'utilisateur

        Args:
            debate_result: Résultat du Pipeline 3

        Returns:
            str: Débat formaté pour affichage
        """
        response_parts = []

        def ensure_string(value):
            """Convertit n'importe quelle valeur en string"""
            if isinstance(value, str):
                return value
            elif isinstance(value, list):
                # Si c'est une liste, joindre récursivement
                return " ".join([ensure_string(v) for v in value])
            else:
                return str(value)

        # Question
        question = debate_result.get("question", "")
        if question:
            response_parts.append(f"**Question** : {ensure_string(question)}\n")

        # Positions identifiées
        position_pour = debate_result.get("position_pour", "")
        position_contre = debate_result.get("position_contre", "")

        if position_pour or position_contre:
            response_parts.append("**📋 Positions du débat**\n")
            if position_pour:
                response_parts.append(f"✅ **Position A** : {ensure_string(position_pour)}")
            if position_contre:
                response_parts.append(f"❌ **Position B** : {ensure_string(position_contre)}\n")

        # Round 1 POUR
        pour_r1 = debate_result.get("pour_round_1", "")
        if pour_r1:
            response_parts.append("\n⚖️ **Round 1 - Arguments POUR**\n")
            response_parts.append(ensure_string(pour_r1))

        # Round 1 CONTRE
        contre_r1 = debate_result.get("contre_round_1", "")
        if contre_r1:
            response_parts.append("\n⚖️ **Round 1 - Arguments CONTRE**\n")
            response_parts.append(ensure_string(contre_r1))

        # Round 2 POUR
        pour_r2 = debate_result.get("pour_round_2", "")
        if pour_r2:
            response_parts.append("\n⚖️ **Round 2 - Réfutation et renforcement POUR**\n")
            response_parts.append(ensure_string(pour_r2))

        # Round 2 CONTRE
        contre_r2 = debate_result.get("contre_round_2", "")
        if contre_r2:
            response_parts.append("\n⚖️ **Round 2 - Réfutation et renforcement CONTRE**\n")
            response_parts.append(ensure_string(contre_r2))

        # Synthèse
        synthese = debate_result.get("synthese", "")
        if synthese:
            response_parts.append("\n🎯 **SYNTHÈSE**\n")
            response_parts.append(ensure_string(synthese))

        # Sources citées
        sources = debate_result.get("sources_citees", [])
        if sources:
            # S'assurer que sources est une liste de strings
            sources_str = []
            for s in sources:
                if isinstance(s, str):
                    sources_str.append(s)
                elif isinstance(s, list):
                    sources_str.extend([str(x) for x in s])
                else:
                    sources_str.append(str(s))
            response_parts.append(f"\n📚 **Sources juridiques citées** : {', '.join(sources_str)}")

        return "\n".join(response_parts)

    def _format_citation_result(self, citation_result: Dict[str, Any]) -> str:
        """
        Formate le résultat des citations pour l'utilisateur

        Args:
            citation_result: Résultat du Pipeline 4

        Returns:
            str: Citations formatées avec explications concises
        """
        response_parts = []

        # Articles de code avec explications
        codes_expliques = citation_result.get("codes_expliques", [])
        if codes_expliques:
            response_parts.append("# Articles de Code\n")
            for code in codes_expliques:
                reference = code.get("reference", "")
                explanation = code.get("explanation", "")
                if reference and explanation:
                    response_parts.append(f"• **{reference}** : {explanation}\n")

        # Jurisprudence avec explications
        juris_expliquee = citation_result.get("jurisprudence_expliquee", [])
        if juris_expliquee:
            response_parts.append("\n# Jurisprudence\n")
            for juris in juris_expliquee:
                reference = juris.get("reference", "")
                explanation = juris.get("explanation", "")
                if reference and explanation:
                    response_parts.append(f"• **{reference}** : {explanation}\n")

        # Résumé
        total_codes = citation_result.get("total_codes", 0)
        total_juris = citation_result.get("total_jurisprudence", 0)
        if total_codes > 0 or total_juris > 0:
            response_parts.append(f"\n**Total** : {total_codes} article(s) de code, {total_juris} jurisprudence(s)")

        return "\n".join(response_parts)
