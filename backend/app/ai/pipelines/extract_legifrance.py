"""
Pipeline 1 : Extraction de textes juridiques depuis Légifrance

Input:
    {
        "message": "Question juridique de l'utilisateur",
        "intention": "DEBAT" | "CITATIONS"
    }

Output:
    {
        "codes": [...],  # Max 5 articles de code
        "jurisprudence": [...],  # Max 5 jurisprudences
        "keywords_used": [...],
        "search_strategy": "precise" | "reformulated" | "broad" | "failed",
        "total_codes": int,
        "total_jurisprudence": int,
        "message": "Message formaté pour l'utilisateur",
        "intention": "DEBAT" | "CITATIONS"
    }
"""

import os
import sys

# Ajouter le répertoire ai au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_dir = os.path.dirname(current_dir)
sys.path.insert(0, ai_dir)

from services.search_service import SearchService


def extract_legifrance(message: str, intention: str) -> dict:
    """
    Pipeline 1 : Extraction de textes juridiques pertinents

    Args:
        message (str): Question de l'utilisateur
        intention (str): DEBAT ou CITATIONS

    Returns:
        dict: Résultats de recherche + message formaté
    """
    print(f"[Pipeline 1] Extraction Légifrance pour intention: {intention}")
    print(f"[Pipeline 1] Message: {message[:100]}...")

    try:
        # Initialiser le service de recherche
        search_service = SearchService()

        # Effectuer la recherche itérative
        result = search_service.search_legal_documents(
            message=message,
            intention=intention
        )

        # Formater le message de retour selon les résultats
        total_results = result["total_codes"] + result["total_jurisprudence"]

        if total_results == 0:
            formatted_message = (
                "Je n'ai pas trouvé de textes juridiques pertinents pour votre question. "
                "Pourriez-vous reformuler ou préciser votre demande ?"
            )
        elif total_results <= 3:
            formatted_message = (
                f"J'ai trouvé {result['total_codes']} article(s) de code et "
                f"{result['total_jurisprudence']} jurisprudence(s) très pertinent(s) pour votre question."
            )
        else:
            formatted_message = (
                f"J'ai trouvé {result['total_codes']} articles de code et "
                f"{result['total_jurisprudence']} jurisprudences pertinentes pour votre question."
            )

        # Ajouter les informations de debug
        result["message"] = formatted_message
        result["intention"] = intention

        print(f"[Pipeline 1] ✅ Succès: {total_results} textes trouvés")
        print(f"[Pipeline 1] Stratégie: {result['search_strategy']}")

        return {"result": result}

    except Exception as e:
        print(f"[Pipeline 1] ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

        return {
            "result": {
                "codes": [],
                "jurisprudence": [],
                "total_codes": 0,
                "total_jurisprudence": 0,
                "keywords_used": [],
                "search_strategy": "error",
                "message": f"Une erreur s'est produite lors de la recherche: {str(e)}",
                "intention": intention,
                "error": str(e)
            }
        }


# Pour les tests locaux
if __name__ == "__main__":
    print("="*80)
    print("TEST PIPELINE 1 - EXTRACTION LÉGIFRANCE")
    print("="*80)

    # Test 1 : Question PACS
    print("\n[TEST 1] Question sur le PACS")
    result1 = extract_legifrance(
        message="Quelles sont les conséquences de la dissolution d'un PACS ?",
        intention="DEBAT"
    )
    print(f"\n📊 Résumé:")
    print(f"  Message: {result1['result']['message']}")
    print(f"  Codes: {result1['result']['total_codes']}")
    print(f"  Jurisprudences: {result1['result']['total_jurisprudence']}")
    print(f"  Stratégie: {result1['result']['search_strategy']}")
    print(f"  Mots-clés: {result1['result']['keywords_used']}")

    # Afficher les codes trouvés
    if result1['result']['codes']:
        print(f"\n📜 CODES TROUVÉS ({len(result1['result']['codes'])}):")
        for i, code in enumerate(result1['result']['codes'], 1):
            print(f"\n  [{i}] Article {code.get('article_num', 'N/A')}")
            print(f"      Code: {code.get('code_title', 'N/A')}")
            print(f"      Date: {code.get('date_version', 'N/A')}")
            print(f"      ID: {code.get('article_id', 'N/A')}")
            print(f"      Texte: {code.get('text_preview', 'N/A')[:200]}...")

    # Afficher les jurisprudences trouvées
    if result1['result']['jurisprudence']:
        print(f"\n⚖️  JURISPRUDENCES TROUVÉES ({len(result1['result']['jurisprudence'])}):")
        for i, juris in enumerate(result1['result']['jurisprudence'], 1):
            print(f"\n  [{i}] {juris.get('title', 'N/A')}")
            print(f"      Date: {juris.get('date', 'N/A')}")
            print(f"      Juridiction: {juris.get('juridiction', 'N/A')}")
            print(f"      ID: {juris.get('decision_id', 'N/A')}")
            print(f"      Texte: {juris.get('text_preview', 'N/A')[:200]}...")

    # Test 2 : Question avec citations
    print("\n" + "="*80)
    print("[TEST 2] Demande de citations sur le mariage")
    print("="*80)
    result2 = extract_legifrance(
        message="Cite-moi les articles du Code civil sur le mariage",
        intention="CITATIONS"
    )
    print(f"\n📊 Résumé:")
    print(f"  Message: {result2['result']['message']}")
    print(f"  Codes: {result2['result']['total_codes']}")
    print(f"  Jurisprudences: {result2['result']['total_jurisprudence']}")
    print(f"  Stratégie: {result2['result']['search_strategy']}")
    print(f"  Mots-clés: {result2['result']['keywords_used']}")

    # Afficher les codes trouvés
    if result2['result']['codes']:
        print(f"\n📜 CODES TROUVÉS ({len(result2['result']['codes'])}):")
        for i, code in enumerate(result2['result']['codes'], 1):
            print(f"\n  [{i}] Article {code.get('article_num', 'N/A')}")
            print(f"      Code: {code.get('code_title', 'N/A')}")
            print(f"      Date: {code.get('date_version', 'N/A')}")
            print(f"      ID: {code.get('article_id', 'N/A')}")
            print(f"      Texte: {code.get('text_preview', 'N/A')[:200]}...")

    # Afficher les jurisprudences trouvées
    if result2['result']['jurisprudence']:
        print(f"\n⚖️  JURISPRUDENCES TROUVÉES ({len(result2['result']['jurisprudence'])}):")
        for i, juris in enumerate(result2['result']['jurisprudence'], 1):
            print(f"\n  [{i}] {juris.get('title', 'N/A')}")
            print(f"      Date: {juris.get('date', 'N/A')}")
            print(f"      Juridiction: {juris.get('juridiction', 'N/A')}")
            print(f"      ID: {juris.get('decision_id', 'N/A')}")
            print(f"      Texte: {juris.get('text_preview', 'N/A')[:200]}...")
