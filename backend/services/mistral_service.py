"""
Service Mistral AI pour l'assistant juridique

Ce service utilise Mistral AI pour:
1. Extraire les concepts juridiques d'une question
2. (À venir) Générer des arguments de débat
"""

import os
from mistralai import Mistral


class MistralService:
    """Service pour interagir avec l'API Mistral AI"""

    def __init__(self):
        """
        Initialise le client Mistral AI

        Charge la clé API depuis les variables d'environnement
        """
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY n'est pas définie dans les variables d'environnement")

        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-latest"

    def extract_legal_concepts(self, question: str) -> dict:
        """
        Extrait les concepts juridiques d'une question en langage naturel

        Cette fonction utilise Mistral pour identifier:
        - Les codes juridiques concernés (Code civil, Code du travail, etc.)
        - Les concepts juridiques principaux (PACS, licenciement, vol, etc.)
        - Le type de documents à rechercher (CODE, LOI, JURISPRUDENCE)

        Args:
            question (str): Question de l'utilisateur en langage naturel

        Returns:
            dict: {
                "question": question originale,
                "search_params": {
                    "codes": ["Code civil"],
                    "concepts": ["PACS", "dissolution", "rupture"],
                    "nature_filter": ["CODE"]
                }
            }

        Example:
            >>> service = MistralService()
            >>> result = service.extract_legal_concepts("Mon mari m'a trompé, on est pacsé")
            >>> print(result["search_params"])
            {
                "codes": ["Code civil"],
                "concepts": ["PACS", "dissolution", "infidélité", "obligations"],
                "nature_filter": ["CODE"]
            }
        """
        print(f"[MistralService] Extraction des concepts juridiques pour: {question}")

        # Prompt pour extraire les concepts juridiques de manière structurée
        prompt = f"""Tu es un expert juridique. Analyse cette question et extrait les informations suivantes au format JSON strict:

Question: {question}

Réponds UNIQUEMENT avec un objet JSON valide (pas de texte avant ou après) avec cette structure:
{{
  "codes": ["liste des codes juridiques concernés"],
  "concepts": ["liste des concepts juridiques clés"],
  "nature_filter": ["liste des types de documents"]
}}

Règles:
- codes: Liste les codes juridiques pertinents (Code civil, Code du travail, Code pénal, Code de commerce)
- concepts: Liste 3-8 termes juridiques clés (noms, pas de verbes)
- nature_filter: Choisis parmi ["CODE", "LOI", "ORDONNANCE", "DECRET", "JURISPRUDENCE"]

Exemples:

Question: "Mon mari m'a trompé, on est pacsé, ai-je des droits ?"
{{
  "codes": ["Code civil"],
  "concepts": ["PACS", "dissolution", "rupture", "infidélité", "obligations", "partenaires"],
  "nature_filter": ["CODE"]
}}

Question: "Mon employeur veut me licencier sans raison"
{{
  "codes": ["Code du travail"],
  "concepts": ["licenciement", "cause réelle", "cause sérieuse", "procédure", "préavis"],
  "nature_filter": ["CODE", "LOI"]
}}

Question: "J'ai volé dans un magasin, quels sont les risques ?"
{{
  "codes": ["Code pénal"],
  "concepts": ["vol", "infraction", "peine", "amende", "prison", "récidive"],
  "nature_filter": ["CODE"]
}}

Maintenant analyse cette question et réponds uniquement avec le JSON:
Question: {question}"""

        try:
            # Appel à Mistral
            response = self.client.chat.complete(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.2,  # Très basse température pour cohérence maximale
                max_tokens=300,
                response_format={"type": "json_object"}  # Force JSON
            )

            # Extraire la réponse JSON
            import json
            content = response.choices[0].message.content.strip()

            print(f"[MistralService] Réponse brute: {content}")

            search_params = json.loads(content)

            # Validation basique
            if "codes" not in search_params or "concepts" not in search_params or "nature_filter" not in search_params:
                raise ValueError("Format JSON invalide de Mistral")

            print(f"[MistralService] Concepts extraits:")
            print(f"  - Codes: {search_params['codes']}")
            print(f"  - Concepts: {search_params['concepts']}")
            print(f"  - Nature: {search_params['nature_filter']}")

            return {
                "question": question,
                "search_params": search_params
            }

        except json.JSONDecodeError as e:
            print(f"[MistralService] Erreur parsing JSON: {e}")
            print(f"[MistralService] Contenu reçu: {content}")

            # Fallback : extraction basique
            return {
                "question": question,
                "search_params": {
                    "codes": ["Code civil"],
                    "concepts": question.split()[:5],  # Premiers mots comme concepts
                    "nature_filter": ["CODE", "LOI"]
                }
            }

        except Exception as e:
            print(f"[MistralService] Erreur lors de l'extraction: {e}")
            raise Exception(f"Erreur Mistral AI: {str(e)}")


# Fonction standalone pour faciliter l'import dans les pipelines
def extract_legal_concepts(question: str) -> dict:
    """
    Fonction utilitaire pour extraire les concepts juridiques

    Args:
        question (str): Question de l'utilisateur

    Returns:
        dict: Concepts juridiques extraits avec search_params
    """
    service = MistralService()
    return service.extract_legal_concepts(question)
