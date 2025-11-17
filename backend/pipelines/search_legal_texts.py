"""
Pipeline CraftAI 2: Recherche des textes juridiques sur Legifrance

Ce pipeline prend les paramètres de recherche extraits par le Pipeline 1
et recherche les articles pertinents sur Legifrance avec leur texte complet.
"""

import sys
sys.path.append('/app')

from services.legifrance_service import LegifranceService


def search_legal_texts(codes: list, concepts: list, nature_filter: list) -> dict:
    """
    Recherche les textes juridiques sur Legifrance

    Args:
        codes (list): Liste des codes juridiques (ex: ["Code civil"])
        concepts (list): Liste des concepts juridiques (ex: ["PACS", "dissolution"])
        nature_filter (list): Liste des types de documents (ex: ["CODE"])

    Returns:
        dict: {
            "articles": [
                {
                    "article_id": "LEGIARTI...",
                    "article_num": "Article 515-7",
                    "full_text": "Le texte complet de l'article...",
                    ...
                }
            ]
        }
    """
    print(f"[Pipeline] search_legal_texts appelé")
    print(f"  Codes: {codes}")
    print(f"  Concepts: {concepts}")
    print(f"  Nature filter: {nature_filter}")

    # Construire les search_params
    search_params = {
        "codes": codes,
        "concepts": concepts,
        "nature_filter": nature_filter
    }

    # Rechercher sur Legifrance avec texte complet des 5 meilleurs articles
    service = LegifranceService()
    search_results = service.search(
        search_params=search_params,
        with_full_text=True,
        top_n=5
    )

    print(f"[Pipeline] Nombre de résultats: {len(search_results.get('results', []))}")

    # Extraire les articles avec leur texte complet
    articles = []
    for result in search_results.get('results', []):
        for article in result.get('articles', []):
            if article.get('full_text'):  # Seulement les articles avec texte complet
                articles.append({
                    "article_id": article.get('article_id'),
                    "article_num": article.get('article_num'),
                    "article_title": article.get('article_title'),
                    "full_text": article.get('full_text'),
                    "code": result.get('fond')
                })

    print(f"[Pipeline] Articles avec texte complet: {len(articles)}")

    # CraftAI attend un dict avec la clé "articles" (nom de l'output défini)
    return {
        "articles": articles
    }


# Pour tester localement
if __name__ == "__main__":
    print("=== TEST LOCAL ===")
    test_codes = ["Code civil"]
    test_concepts = ["PACS", "dissolution"]
    test_nature_filter = ["CODE"]

    result = search_legal_texts(test_codes, test_concepts, test_nature_filter)
    print(f"\nNombre d'articles trouvés: {len(result['articles'])}")
    if result['articles']:
        print(f"\nPremier article:")
        print(f"  ID: {result['articles'][0]['article_id']}")
        print(f"  Num: {result['articles'][0]['article_num']}")
        print(f"  Texte: {result['articles'][0]['full_text'][:200]}...")
