"""
Pipeline 4 : Citations juridiques avec explications concises

Input:
    {
        "message": "Question juridique de l'utilisateur",
        "legal_data": {
            "codes": [...],
            "jurisprudence": [...],
            "total_codes": int,
            "total_jurisprudence": int
        }
    }

Output:
    {
        "question": "Question originale",
        "codes_expliques": [
            {
                "reference": "Article X du Code Y",
                "explanation": "Explication brève"
            }
        ],
        "jurisprudence_expliquee": [
            {
                "reference": "Cour, date",
                "explanation": "Explication brève"
            }
        ],
        "total_codes": int,
        "total_jurisprudence": int
    }
"""

import os
import sys
import json

# Ajouter le répertoire ai au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_dir = os.path.dirname(current_dir)
sys.path.insert(0, ai_dir)

from services.citation_service import CitationService


def citation(message: str, legal_data: dict) -> dict:
    """
    Pipeline 4 : Génère des explications concises pour chaque citation juridique

    Args:
        message (str): Question de l'utilisateur
        legal_data (dict): Données juridiques de P1 (codes + jurisprudence)

    Returns:
        dict: Citations avec explications brèves
    """
    print(f"[Pipeline 4] ===== DEBUT PIPELINE CITATION =====")
    print(f"[Pipeline 4] Message type: {type(message)}, value: {message[:100] if message else 'NONE'}...")
    print(f"[Pipeline 4] Legal_data type: {type(legal_data)}")
    print(f"[Pipeline 4] Legal_data keys: {list(legal_data.keys()) if legal_data else 'NONE'}")
    print(f"[Pipeline 4] Sources: {legal_data.get('total_codes', 0)} codes, {legal_data.get('total_jurisprudence', 0)} jurisprudences")

    try:
        # Vérifier qu'on a des données juridiques
        codes = legal_data.get("codes", [])
        jurisprudence = legal_data.get("jurisprudence", [])

        if not codes and not jurisprudence:
            print("[Pipeline 4] ⚠️  Aucune source juridique fournie")
            # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
            return {
                "result": {
                    "question": message,
                    "codes_expliques": [],
                    "jurisprudence_expliquee": [],
                    "total_codes": 0,
                    "total_jurisprudence": 0,
                    "error": "no_sources"
                }
            }

        # Initialiser le service de citation
        citation_service = CitationService()

        # Générer les citations avec explications
        citation_result = citation_service.generate_citations(message, legal_data)

        print(f"[Pipeline 4] ✅ Citations générées avec succès")
        print(f"  Codes expliqués: {len(citation_result.get('codes_expliques', []))}")
        print(f"  Jurisprudences expliquées: {len(citation_result.get('jurisprudence_expliquee', []))}")

        # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
        return {"result": citation_result}

    except Exception as e:
        print(f"[Pipeline 4] ❌ Erreur lors de la génération des citations: {e}")
        import traceback
        traceback.print_exc()

        # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
        return {
            "result": {
                "question": message,
                "codes_expliques": [],
                "jurisprudence_expliquee": [],
                "total_codes": 0,
                "total_jurisprudence": 0,
                "error": str(e)
            }
        }


# Point d'entrée pour CraftAI
if __name__ == "__main__":
    # Test local
    test_message = "Quelles sont les conditions de dissolution d'un PACS ?"
    test_legal_data = {
        "codes": [
            {
                "type": "CODE",
                "code_title": "Code civil",
                "article_num": "515-7",
                "article_id": "LEGIARTI000033460726",
                "text_preview": "Le pacte civil de solidarité se dissout par la mort de l'un des partenaires ou par le mariage.",
                "legal_status": "VIGUEUR"
            },
            {
                "type": "CODE",
                "code_title": "Code civil",
                "article_num": "515-4",
                "article_id": "LEGIARTI000006421588",
                "text_preview": "Les partenaires liés par un pacte civil de solidarité s'engagent à une vie commune ainsi qu'à une aide matérielle et une assistance réciproques.",
                "legal_status": "VIGUEUR"
            }
        ],
        "jurisprudence": [
            {
                "type": "JURIS",
                "title": "Cour de cassation, civile, Chambre civile 1, 27 janvier 2021, 19-26.140",
                "text_preview": "L'aide matérielle entre partenaires est une obligation fondamentale du PACS."
            }
        ],
        "total_codes": 2,
        "total_jurisprudence": 1
    }

    result = citation(test_message, test_legal_data)
    print("\n" + "="*80)
    print("RÉSULTAT DES CITATIONS:")
    print("="*80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
