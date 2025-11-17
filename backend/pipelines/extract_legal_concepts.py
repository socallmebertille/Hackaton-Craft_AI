"""
Pipeline CraftAI 1: Extraction des concepts juridiques

Ce pipeline prend une question juridique et extrait:
- Les codes juridiques concernés
- Les concepts juridiques clés
- Le filtre de nature des documents
"""

import sys
sys.path.append('/app')

from services.mistral_service import MistralService


def extract_legal_concepts(question: str) -> dict:
    """
    Extrait les concepts juridiques d'une question pour Legifrance

    Args:
        question (str): Question juridique posée par l'utilisateur

    Returns:
        dict: {
            "question": "...",
            "search_params": {
                "codes": ["Code civil"],
                "concepts": ["PACS", "dissolution"],
                "nature_filter": ["CODE"]
            }
        }
    """
    print(f"[Pipeline] extract_legal_concepts appelé avec question={question}")

    service = MistralService()
    extraction_result = service.extract_legal_concepts(question)

    print(f"[Pipeline] Concepts extraits: {extraction_result['search_params']}")

    # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
    return {
        "result": extraction_result
    }


# Pour tester localement (avant de l'uploader sur CraftAI)
if __name__ == "__main__":
    print("=== TEST LOCAL ===")
    test_question = "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?"
    result = extract_legal_concepts(test_question)
    print(f"Résultat: {result}")
