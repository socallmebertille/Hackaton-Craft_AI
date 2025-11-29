"""
Test de la recherche Légifrance améliorée

Teste que la nouvelle stratégie de recherche (TOUS_LES_MOTS au lieu de UN_DES_MOTS)
retourne des articles pertinents pour la question posée.
"""

import sys
import os

# Ajouter le répertoire backend au path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.mistral_service import MistralService
from services.legifrance_service import LegifranceService


def test_pacs_dissolution():
    """
    Test avec la question sur le PACS qui posait problème
    """
    print("\n" + "="*100)
    print("🧪 TEST: Recherche Légifrance améliorée - Question sur le PACS")
    print("="*100)

    question = "Quelles sont les lois sur la dissolution du PACS ?"
    print(f"\n📝 Question: {question}\n")

    # Étape 1: Extraction des concepts avec le nouveau prompt
    print("="*100)
    print("ÉTAPE 1: Extraction des concepts juridiques (P1)")
    print("="*100)

    mistral = MistralService()
    extraction = mistral.extract_legal_concepts(question)

    search_params = extraction["search_params"]

    # Ajouter la question dans search_params (comme le fait P1)
    search_params['question'] = question

    print(f"\n✅ Concepts extraits:")
    print(f"   - Codes: {search_params['codes']}")
    print(f"   - Concepts: {search_params['concepts']}")
    print(f"   - Nature: {search_params['nature_filter']}")

    # Étape 2: Recherche sur Légifrance avec nouvelle stratégie
    print("\n" + "="*100)
    print("ÉTAPE 2: Recherche sur Légifrance (P2)")
    print("="*100)

    legifrance = LegifranceService()
    results = legifrance.search(
        search_params=search_params,
        with_full_text=True,
        top_n=5
    )

    total = results.get("total", 0)
    query = results.get("query", "")
    legifrance_results = results.get("results", [])

    print(f"\n✅ Recherche Légifrance:")
    print(f"   - Query envoyée: '{query}'")
    print(f"   - Total résultats: {total}")
    print(f"   - Résultats groupés: {len(legifrance_results)}")

    # Étape 3: Afficher les articles trouvés
    print("\n" + "="*100)
    print("ÉTAPE 3: Articles trouvés")
    print("="*100)

    articles_count = 0
    for result in legifrance_results:
        code_name = result.get("code_title", "Code inconnu")
        articles = result.get("articles", [])

        print(f"\n📖 Code: {code_name}")
        print(f"   Nombre d'articles: {len(articles)}")

        for i, article in enumerate(articles[:5], 1):  # Afficher les 5 premiers
            article_num = article.get("article_num", "N/A")
            full_text = article.get("full_text", "")
            text_preview = article.get("text_preview", "")

            print(f"\n   [{i}] Article {article_num}")

            # Afficher un aperçu du texte
            text_to_show = full_text if full_text else text_preview
            if text_to_show:
                # Vérifier si le texte contient bien "PACS" ou "pacte civil"
                contains_pacs = "pacs" in text_to_show.lower() or "pacte civil" in text_to_show.lower()
                relevance_icon = "✅" if contains_pacs else "⚠️"

                print(f"   {relevance_icon} Texte: {text_to_show[:200]}...")
                if not contains_pacs:
                    print(f"   ⚠️ ATTENTION: Cet article ne semble pas parler du PACS!")

            articles_count += 1

    # Vérification finale
    print("\n" + "="*100)
    print("RÉSULTAT DU TEST")
    print("="*100)

    if articles_count > 0:
        print(f"✅ {articles_count} articles trouvés")
        print(f"\nVérifie visuellement ci-dessus que:")
        print(f"  - Les articles contiennent bien le mot 'PACS'")
        print(f"  - Les articles parlent de dissolution/rupture du PACS")
        print(f"  - Aucun article hors-sujet (sociétés, contrats non-PACS, etc.)")
    else:
        print(f"❌ Aucun article trouvé - Il y a un problème!")

    print("="*100 + "\n")


if __name__ == "__main__":
    test_pacs_dissolution()
