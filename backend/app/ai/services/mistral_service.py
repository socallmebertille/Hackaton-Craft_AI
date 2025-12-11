"""
Service Mistral AI pour l'analyse d'intention et l'extraction de mots-clés juridiques
"""

import os
import json
from mistralai import Mistral
from typing import Literal, List, Dict


# Types d'intention possibles
IntentionType = Literal["DEBAT", "CITATIONS", "HORS_SUJET"]


class MistralService:
    """Service pour interagir avec l'API Mistral AI"""

    def __init__(self):
        """Initialise le client Mistral"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY n'est pas définie dans les variables d'environnement")

        self.client = Mistral(api_key=api_key)
        self.model = os.getenv("MISTRAL_MODEL_SMALL", "mistral-small-latest")
        print(f"[MistralService] Initialisé avec le modèle: {self.model}")

    def analyze_intent(self, message: str) -> dict:
        """
        Analyse l'intention de l'utilisateur à partir de son message

        Args:
            message (str): Message de l'utilisateur

        Returns:
            dict: {
                "message": "...",
                "intention": "DEBAT" | "CITATIONS" | "HORS_SUJET",
                "confidence": 0.95,
                "reasoning": "Explication de l'analyse"
            }
        """
        print(f"[MistralService] Analyse d'intention pour: {message[:100]}...")

        # Prompt système pour l'analyse d'intention
        system_prompt = """Tu es un assistant juridique expert qui analyse l'intention des utilisateurs.

Ton rôle est de déterminer ce que l'utilisateur souhaite obtenir :

1. **DEBAT** : L'utilisateur veut une discussion approfondie, une explication détaillée, une analyse juridique, des conseils, ou comprendre un concept juridique.
   - Exemples : "Explique-moi...", "Quelles sont les conséquences...", "Comment fonctionne...", "Qu'est-ce que...", "Peux-tu m'aider à comprendre..."

2. **CITATIONS** : L'utilisateur cherche des références précises, des articles de loi, de la jurisprudence, des textes officiels.
   - Exemples : "Cite-moi les articles...", "Quels sont les textes de loi...", "Jurisprudence sur...", "Références légales concernant..."

3. **HORS_SUJET** : Le message n'est pas lié au domaine juridique ou est inapproprié.
   - Exemples : Questions personnelles, blagues, sujets non juridiques, spam, etc.

Réponds UNIQUEMENT avec un JSON valide au format suivant :
{
    "intention": "DEBAT" | "CITATIONS" | "HORS_SUJET",
    "confidence": 0.0 à 1.0,
    "reasoning": "Brève explication de ton analyse"
}"""

        user_prompt = f"Message de l'utilisateur : \"{message}\"\n\nAnalyse l'intention de ce message."

        try:
            # Appel à l'API Mistral
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Faible température pour plus de cohérence
                response_format={"type": "json_object"}
            )

            # Extraire le contenu de la réponse
            content = response.choices[0].message.content
            analysis = json.loads(content)

            # Valider la structure de la réponse
            if "intention" not in analysis or analysis["intention"] not in ["DEBAT", "CITATIONS", "HORS_SUJET"]:
                raise ValueError(f"Intention invalide: {analysis.get('intention')}")

            result = {
                "message": message,
                "intention": analysis["intention"],
                "confidence": analysis.get("confidence", 0.8),
                "reasoning": analysis.get("reasoning", "")
            }

            print(f"[MistralService] Intention détectée: {result['intention']} (confiance: {result['confidence']})")
            return result

        except Exception as e:
            print(f"[MistralService] Erreur lors de l'analyse: {e}")
            # Fallback en cas d'erreur
            return {
                "message": message,
                "intention": "DEBAT",  # Par défaut, on considère que c'est un débat
                "confidence": 0.5,
                "reasoning": f"Erreur lors de l'analyse: {str(e)}"
            }

    def extract_keywords(self, message: str, intention: str) -> Dict[str, any]:
        """
        Extrait les mots-clés juridiques optimisés pour la recherche Légifrance

        Args:
            message (str): Question de l'utilisateur
            intention (str): DEBAT ou CITATIONS

        Returns:
            dict: {
                "keywords": ["pacte civil de solidarité", "dissolution"],
                "codes": ["Code civil"],
                "concepts": ["PACS", "rupture", "séparation"]
            }
        """
        print(f"[MistralService] Extraction de mots-clés pour: {message[:100]}...")

        system_prompt = """Tu es un expert juridique qui extrait des mots-clés optimisés pour rechercher dans la base de données juridique Légifrance.

IMPORTANT : Les textes de loi utilisent souvent des termes officiels complets, pas les abréviations courantes.
- Exemple : "PACS" → utilise "pacte civil de solidarité" (terme officiel dans le Code civil)
- Exemple : "CDI" → utilise "contrat à durée indéterminée"
- Exemple : "licenciement" → garde tel quel (terme officiel)

Ton rôle :
1. Identifier les **concepts juridiques principaux** (2-4 concepts max)
2. Les transformer en **termes juridiques officiels** quand nécessaire
3. Suggérer les **codes concernés** (Code civil, Code pénal, Code du travail, etc.)

Réponds UNIQUEMENT avec un JSON valide :
{
    "keywords": ["terme officiel 1", "terme officiel 2"],  // 2-4 mots-clés max, termes officiels
    "codes": ["Code civil"],  // 1-2 codes max, ou [] si incertain
    "concepts": ["concept1", "concept2"],  // Concepts originaux de la question
    "reasoning": "Explication rapide de tes choix"
}"""

        user_prompt = f"""Question de l'utilisateur : "{message}"
Intention : {intention}

Extrais les mots-clés optimisés pour rechercher dans Légifrance."""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Valider la structure
            if "keywords" not in result or not isinstance(result["keywords"], list):
                raise ValueError("Structure invalide: 'keywords' manquant ou invalide")

            print(f"[MistralService] Mots-clés extraits: {result['keywords']}")
            print(f"[MistralService] Codes suggérés: {result.get('codes', [])}")

            return result

        except Exception as e:
            print(f"[MistralService] Erreur extraction mots-clés: {e}")
            # Fallback : extraire des mots simples de la question
            words = message.lower().split()
            keywords = [w for w in words if len(w) > 4][:3]

            return {
                "keywords": keywords,
                "codes": [],
                "concepts": keywords,
                "reasoning": f"Erreur: {str(e)}"
            }


# Pour tester localement
if __name__ == "__main__":
    import sys

    # Test du service
    service = MistralService()

    test_messages = [
        "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?",
        "Cite-moi les articles du Code civil sur le PACS",
        "Quel est ton plat préféré ?",
        "Comment puis-je contester un licenciement abusif ?",
        "Donne-moi la jurisprudence récente sur le droit au logement"
    ]

    print("\n" + "="*80)
    print("TESTS DU SERVICE D'ANALYSE D'INTENTION")
    print("="*80 + "\n")

    for msg in test_messages:
        print(f"Message: {msg}")
        result = service.analyze_intent(msg)
        print(f"  → Intention: {result['intention']}")
        print(f"  → Confiance: {result['confidence']}")
        print(f"  → Raisonnement: {result['reasoning']}")
        print()
