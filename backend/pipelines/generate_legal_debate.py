"""
Pipeline CraftAI 3: Génération du débat juridique contradictoire

Ce pipeline prend les articles juridiques trouvés par le Pipeline 2
et génère un débat en 2 rounds avec thèse/antithèse croisées.
"""

import sys
sys.path.append('/app')

from services.mistral_debate_service import MistralDebateService
from typing import List


def generate_legal_debate(question: str, articles: List[dict]) -> dict:
    """
    Génère un débat juridique contradictoire en 2 rounds

    Args:
        question (str): Question juridique posée par l'utilisateur
        articles (list): Liste des articles avec leur texte complet
            [
                {
                    "article_id": "LEGIARTI...",
                    "article_num": "515-7",
                    "full_text": "Le texte complet...",
                    ...
                }
            ]

    Returns:
        dict: {
            "debate": {
                "question": "...",
                "round_1": {
                    "these": "Argument initial en faveur",
                    "antithese": "Argument initial contre"
                },
                "round_2": {
                    "these": "Répond à l'antithèse du round 1",
                    "antithese": "Répond à la thèse du round 1"
                },
                "synthese": "Analyse finale des 2 rounds...",
                "articles_used": [...]
            }
        }
    """
    print(f"[Pipeline] generate_legal_debate appelé")
    print(f"  Question: {question}")
    print(f"  Nombre d'articles: {len(articles)}")

    # Générer le débat avec Mistral
    service = MistralDebateService()
    debate_result = service.generate_debate(question=question, articles=articles)

    print(f"[Pipeline] Débat généré avec succès")
    print(f"  Round 1 - Thèse: {len(debate_result['round_1']['these'])} caractères")
    print(f"  Round 1 - Antithèse: {len(debate_result['round_1']['antithese'])} caractères")
    print(f"  Round 2 - Thèse: {len(debate_result['round_2']['these'])} caractères")
    print(f"  Round 2 - Antithèse: {len(debate_result['round_2']['antithese'])} caractères")
    print(f"  Synthèse: {len(debate_result['synthese'])} caractères")

    # CraftAI attend un dict avec la clé "debate" (nom de l'output défini)
    return {
        "debate": debate_result
    }


# Pour tester localement
if __name__ == "__main__":
    print("=== TEST LOCAL ===")

    test_question = "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?"

    # Articles de test (simulés)
    test_articles = [
        {
            "article_id": "LEGIARTI000006444164",
            "article_num": "1844-5",
            "full_text": "La réunion de toutes les parts sociales en une seule main n'entraîne pas la dissolution de plein droit de la société. Tout intéressé peut demander cette dissolution si la situation n'a pas été régularisée dans le délai d'un an. Le tribunal peut accorder à la société un délai maximal de six mois pour régulariser la situation. Il ne peut prononcer la dissolution si, au jour où il statue sur le fond, cette régularisation a eu lieu."
        },
        {
            "article_id": "LEGIARTI000006444172",
            "article_num": "1844-7",
            "full_text": "La société prend fin : 1° Par l'expiration du temps pour lequel elle a été constituée, sauf prorogation effectuée conformément à l'article 1844-6 ; 2° Par la réalisation ou l'extinction de son objet ; 3° Par l'annulation du contrat de société ; 4° Par la dissolution anticipée décidée par les associés ; 5° Par la dissolution anticipée prononcée par le tribunal à la demande d'un associé pour justes motifs, notamment en cas d'inexécution de ses obligations par un associé, ou de mésintelligence entre associés paralysant le fonctionnement de la société."
        }
    ]

    result = generate_legal_debate(test_question, test_articles)

    print(f"\n📊 Résultat:")
    print(f"   Question: {result['debate']['question']}")
    print(f"\n   Round 1:")
    print(f"     Thèse: {result['debate']['round_1']['these'][:150]}...")
    print(f"     Antithèse: {result['debate']['round_1']['antithese'][:150]}...")
    print(f"\n   Round 2:")
    print(f"     Thèse: {result['debate']['round_2']['these'][:150]}...")
    print(f"     Antithèse: {result['debate']['round_2']['antithese'][:150]}...")
    print(f"\n   Synthèse: {result['debate']['synthese'][:150]}...")
