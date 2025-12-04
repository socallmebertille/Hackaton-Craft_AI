"""
Pipeline CraftAI: Analyse de l'intention utilisateur

Ce pipeline prend un message utilisateur et détermine son intention:
- DEBAT: L'utilisateur veut une discussion/explication approfondie
- CITATIONS: L'utilisateur cherche des références légales précises
- HORS_SUJET: Le message n'est pas lié au domaine juridique

Input: message (str)
Output: result (dict) avec {message, intention, confidence, reasoning}
"""

import sys
import os

# Ajouter le chemin du dossier ai au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_dir = os.path.dirname(current_dir)
sys.path.insert(0, ai_dir)

from services.mistral_service import MistralService


def analyze_intent(message: str) -> dict:
    """
    Analyse l'intention d'un message utilisateur

    Args:
        message (str): Message/question de l'utilisateur

    Returns:
        dict: {
            "result": {
                "message": "...",
                "intention": "DEBAT" | "CITATIONS" | "HORS_SUJET",
                "confidence": 0.95,
                "reasoning": "Explication"
            }
        }
    """
    print(f"[Pipeline] analyze_intent appelé avec message={message[:100]}...")

    # Initialiser le service Mistral
    service = MistralService()

    # Analyser l'intention
    analysis_result = service.analyze_intent(message)

    print(f"[Pipeline] Intention détectée: {analysis_result['intention']} (confiance: {analysis_result['confidence']})")

    # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
    return {
        "result": analysis_result
    }


# Pour tester localement (avant de l'uploader sur CraftAI)
if __name__ == "__main__":
    print("=" * 80)
    print("TEST LOCAL - Pipeline analyze_intent")
    print("=" * 80 + "\n")

    test_messages = [
        "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?",
        "Cite-moi les articles du Code civil concernant le mariage",
        "Quel temps fait-il aujourd'hui ?",
        "Comment puis-je contester un licenciement abusif ?",
        "Donne-moi la jurisprudence sur le droit au logement"
    ]

    for msg in test_messages:
        print(f"\n📝 Message: {msg}")
        result = analyze_intent(msg)
        print(f"✅ Résultat: {result['result']}")
        print("-" * 80)
