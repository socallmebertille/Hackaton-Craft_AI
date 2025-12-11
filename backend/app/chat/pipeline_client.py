"""
Client pour les appels aux pipelines CraftAI

Gère tous les appels HTTP vers les 4 pipelines :
- Pipeline 0: Analyse d'intention
- Pipeline 1: Extraction Légifrance
- Pipeline 3: Débat juridique
- Pipeline 4: Citations avec explications
"""

import httpx
from typing import Dict, Any, Optional
from app.core.config import settings


class PipelineClient:
    """Client pour communiquer avec les pipelines CraftAI"""

    def __init__(self):
        """Initialise le client avec les configurations des pipelines"""
        # Pipeline 0: Analyse d'intention
        self.pipeline_0_url = settings.PIPELINE_0_ENDPOINT_URL
        self.pipeline_0_token = settings.PIPELINE_0_ENDPOINT_TOKEN

        # Pipeline 1: Extraction Légifrance
        self.pipeline_1_url = settings.PIPELINE_1_ENDPOINT_URL
        self.pipeline_1_token = settings.PIPELINE_1_ENDPOINT_TOKEN

        # Pipeline 3: Débat juridique
        self.pipeline_3_url = settings.PIPELINE_3_ENDPOINT_URL
        self.pipeline_3_token = settings.PIPELINE_3_ENDPOINT_TOKEN

        # Pipeline 4: Citations avec explications
        self.pipeline_4_url = settings.PIPELINE_4_ENDPOINT_URL
        self.pipeline_4_token = settings.PIPELINE_4_ENDPOINT_TOKEN

    async def call_pipeline_0(self, message: str) -> Optional[Dict[str, Any]]:
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
                    print(f"[PipelineClient] Pipeline 0 failed: {data}")
                    return None

                return data.get("outputs", {}).get("result", {}).get("value")

        except httpx.HTTPError as e:
            print(f"[PipelineClient] Erreur HTTP lors de l'appel au Pipeline 0: {e}")
            return None
        except Exception as e:
            print(f"[PipelineClient] Erreur lors de l'appel au Pipeline 0: {e}")
            return None

    async def call_pipeline_1(self, message: str, intention: str) -> Optional[Dict[str, Any]]:
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
                    print(f"[PipelineClient] Pipeline 1 failed: {data}")
                    return None

                return data.get("outputs", {}).get("result", {}).get("value")

        except httpx.HTTPError as e:
            print(f"[PipelineClient] Erreur HTTP lors de l'appel au Pipeline 1: {e}")
            return None
        except Exception as e:
            print(f"[PipelineClient] Erreur lors de l'appel au Pipeline 1: {e}")
            return None

    async def call_pipeline_3(self, message: str, legal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Appelle le Pipeline 3 (débat juridique)

        Args:
            message: Message de l'utilisateur
            legal_data: Données juridiques de P1

        Returns:
            dict: Résultat du débat ou None si erreur
        """
        try:
            print(f"[PipelineClient] Appel Pipeline 3 avec {legal_data.get('total_codes', 0)} codes et {legal_data.get('total_jurisprudence', 0)} jurisprudences")

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
                    print(f"[PipelineClient] Pipeline 3 failed: {data}")
                    return None

                result = data.get("outputs", {}).get("result", {}).get("value")

                if result:
                    print(f"[PipelineClient] Pipeline 3 succeeded - Position POUR: {result.get('position_pour', '')[:50]}...")
                else:
                    print(f"[PipelineClient] Pipeline 3 returned null result")

                return result

        except httpx.HTTPError as e:
            print(f"[PipelineClient] Erreur HTTP lors de l'appel au Pipeline 3: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[PipelineClient] Response body: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"[PipelineClient] Erreur lors de l'appel au Pipeline 3: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def call_pipeline_4(self, message: str, legal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                print("[PipelineClient] Pipeline 4 non configuré")
                return None

            print(f"[PipelineClient] Appel Pipeline 4 avec {legal_data.get('total_codes', 0)} codes et {legal_data.get('total_jurisprudence', 0)} jurisprudences")

            # Loguer un échantillon des données pour debug
            import json
            if legal_data.get('jurisprudence'):
                print(f"[PipelineClient] Échantillon jurisprudence[0]: {json.dumps(legal_data['jurisprudence'][0], indent=2, default=str)[:300]}...")

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
                    print(f"[PipelineClient] Pipeline 4 failed: {data}")
                    return None

                result = data.get("outputs", {}).get("result", {}).get("value")

                if result:
                    print(f"[PipelineClient] Pipeline 4 succeeded - {len(result.get('codes_expliques', []))} codes expliqués")
                else:
                    print(f"[PipelineClient] Pipeline 4 returned null result")

                return result

        except httpx.HTTPError as e:
            print(f"[PipelineClient] Erreur HTTP lors de l'appel au Pipeline 4: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[PipelineClient] Response body: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"[PipelineClient] Erreur lors de l'appel au Pipeline 4: {e}")
            import traceback
            traceback.print_exc()
            return None
