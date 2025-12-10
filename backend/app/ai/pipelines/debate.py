"""
Pipeline 3 : Débat juridique contradictoire

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
        "position_pour": "Description position A",
        "position_contre": "Description position B",
        "pour_round_1": "Arguments POUR round 1",
        "contre_round_1": "Arguments CONTRE round 1",
        "pour_round_2": "Arguments POUR round 2",
        "contre_round_2": "Arguments CONTRE round 2",
        "synthese": "Synthèse équilibrée",
        "sources_citees": ["CODE 1", "JURIS 2", ...],
        "total_arguments_pour": int,
        "total_arguments_contre": int
    }
"""

import os
import sys
import json

# Ajouter le répertoire ai au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_dir = os.path.dirname(current_dir)
sys.path.insert(0, ai_dir)

from services.debate_service import DebateService


def debate(message: str, legal_data: dict) -> dict:
    """
    Pipeline 3 : Génère un débat contradictoire sur une question juridique

    Args:
        message (str): Question de l'utilisateur
        legal_data (dict): Données juridiques de P1 (codes + jurisprudence)

    Returns:
        dict: Débat structuré avec rounds pour/contre + synthèse
    """
    print(f"[Pipeline 3] ===== DEBUT PIPELINE DEBATE =====")
    print(f"[Pipeline 3] Message type: {type(message)}, value: {message[:100] if message else 'NONE'}...")
    print(f"[Pipeline 3] Legal_data type: {type(legal_data)}")
    print(f"[Pipeline 3] Legal_data keys: {list(legal_data.keys()) if legal_data else 'NONE'}")
    print(f"[Pipeline 3] Sources: {legal_data.get('total_codes', 0)} codes, {legal_data.get('total_jurisprudence', 0)} jurisprudences")

    try:
        # Vérifier qu'on a des données juridiques
        codes = legal_data.get("codes", [])
        jurisprudence = legal_data.get("jurisprudence", [])

        if not codes and not jurisprudence:
            print("[Pipeline 3] ⚠️  Aucune source juridique fournie")
            # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
            return {
                "result": {
                    "question": message,
                    "position_pour": "",
                    "position_contre": "",
                    "pour_round_1": "",
                    "contre_round_1": "",
                    "pour_round_2": "",
                    "contre_round_2": "",
                    "synthese": "Impossible de générer un débat : aucune source juridique disponible.",
                    "sources_citees": [],
                    "total_arguments_pour": 0,
                    "total_arguments_contre": 0,
                    "error": "no_sources"
                }
            }

        # Initialiser le service de débat
        debate_service = DebateService()

        # Générer le débat
        debate_result = debate_service.generate_debate(message, legal_data)

        # Enrichir la réponse
        debate_result["question"] = message
        debate_result["total_arguments_pour"] = 4  # 2 rounds pour
        debate_result["total_arguments_contre"] = 4  # 2 rounds contre

        print(f"[Pipeline 3] ✅ Débat généré avec succès")
        print(f"  Position POUR: {debate_result.get('position_pour', '')[:60]}...")
        print(f"  Position CONTRE: {debate_result.get('position_contre', '')[:60]}...")
        print(f"  Sources utilisées: {len(debate_result.get('sources_citees', []))}")

        # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
        return {"result": debate_result}

    except Exception as e:
        print(f"[Pipeline 3] ❌ Erreur lors de la génération du débat: {e}")
        import traceback
        traceback.print_exc()

        # CraftAI attend un dict avec la clé "result" (nom de l'output défini)
        return {
            "result": {
                "question": message,
                "position_pour": "",
                "position_contre": "",
                "pour_round_1": "",
                "contre_round_1": "",
                "pour_round_2": "",
                "contre_round_2": "",
                "synthese": f"Erreur lors de la génération du débat: {str(e)}",
                "sources_citees": [],
                "total_arguments_pour": 0,
                "total_arguments_contre": 0,
                "error": str(e)
            }
        }


# Point d'entrée pour CraftAI
if __name__ == "__main__":
    # Test local
    test_message = "Quelles sont les conséquences de la dissolution d'un PACS ?"
    test_legal_data = {
        "codes": [
            {
                "type": "CODE",
                "code_title": "Code civil",
                "article_num": "515-7",
                "article_id": "LEGIARTI000033460726",
                "text_preview": "Le pacte civil de solidarité se dissout par la mort de l'un des partenaires ou par le mariage.",
                "legal_status": "VIGUEUR"
            }
        ],
        "jurisprudence": [],
        "total_codes": 1,
        "total_jurisprudence": 0
    }

    result = debate(test_message, test_legal_data)
    print("\n" + "="*80)
    print("RÉSULTAT DU DÉBAT:")
    print("="*80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
