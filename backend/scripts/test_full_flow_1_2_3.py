"""
Test du flux complet: Pipeline 1 → Pipeline 2 → Pipeline 3
Question → Extraction concepts → Recherche Legifrance → Débat contradictoire
"""

import requests
import os

# Configuration depuis les variables d'environnement
PIPELINE_1_URL = os.getenv("CRAFTAI_PIPELINE_1_URL")
PIPELINE_1_TOKEN = os.getenv("CRAFTAI_PIPELINE_1_TOKEN")
PIPELINE_2_URL = os.getenv("CRAFTAI_PIPELINE_2_URL")
PIPELINE_2_TOKEN = os.getenv("CRAFTAI_PIPELINE_2_TOKEN")
PIPELINE_3_URL = os.getenv("CRAFTAI_PIPELINE_3_URL")
PIPELINE_3_TOKEN = os.getenv("CRAFTAI_PIPELINE_3_TOKEN")

# Vérification que les variables d'environnement sont définies
if not all([PIPELINE_1_URL, PIPELINE_1_TOKEN, PIPELINE_2_URL, PIPELINE_2_TOKEN, PIPELINE_3_URL, PIPELINE_3_TOKEN]):
    print("❌ ERREUR: Les variables d'environnement CraftAI ne sont pas toutes définies")
    print("Vérifiez que le .env contient:")
    print("  - CRAFTAI_PIPELINE_1_URL et CRAFTAI_PIPELINE_1_TOKEN")
    print("  - CRAFTAI_PIPELINE_2_URL et CRAFTAI_PIPELINE_2_TOKEN")
    print("  - CRAFTAI_PIPELINE_3_URL et CRAFTAI_PIPELINE_3_TOKEN")
    exit(1)

print("="*80)
print("Test du flux complet: Pipeline 1 → Pipeline 2 → Pipeline 3")
print("="*80)

# Question de test
test_question = "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?"

print(f"\n📝 Question: {test_question}")

# ============================================================================
# ÉTAPE 1: Extraction des concepts (Pipeline 1)
# ============================================================================
print(f"\n" + "="*80)
print("ÉTAPE 1: Extraction des concepts juridiques (Pipeline 1)")
print("="*80)

print(f"\n🚀 Appel du Pipeline 1...")

response_1 = requests.post(
    PIPELINE_1_URL,
    json={"question": test_question},
    headers={"Authorization": f"EndpointToken {PIPELINE_1_TOKEN}"},
)

if not response_1.ok:
    print(f"\n❌ ERREUR Pipeline 1: {response_1.status_code}")
    print(response_1.text)
    exit(1)

result_1 = response_1.json()
print(f"\n✅ Pipeline 1 terminé !")

# Extraire les search_params
extraction_data = result_1["outputs"]["result"]["value"]
codes = extraction_data["search_params"]["codes"]
concepts = extraction_data["search_params"]["concepts"]
nature_filter = extraction_data["search_params"]["nature_filter"]

print(f"\n📊 Concepts extraits:")
print(f"   Codes: {codes}")
print(f"   Concepts: {concepts}")
print(f"   Nature filter: {nature_filter}")

# ============================================================================
# ÉTAPE 2: Recherche Legifrance (Pipeline 2)
# ============================================================================
print(f"\n" + "="*80)
print("ÉTAPE 2: Recherche des textes juridiques sur Legifrance (Pipeline 2)")
print("="*80)

print(f"\n🚀 Appel du Pipeline 2...")

response_2 = requests.post(
    PIPELINE_2_URL,
    json={
        "codes": codes,
        "concepts": concepts,
        "nature_filter": nature_filter
    },
    headers={"Authorization": f"EndpointToken {PIPELINE_2_TOKEN}"},
)

if not response_2.ok:
    print(f"\n❌ ERREUR Pipeline 2: {response_2.status_code}")
    print(response_2.text)
    exit(1)

result_2 = response_2.json()
print(f"\n✅ Pipeline 2 terminé !")

# Extraire les articles
articles = result_2["outputs"]["articles"]["value"]

print(f"\n📊 Articles trouvés: {len(articles)}")

if articles:
    print(f"\n📄 Aperçu des articles:")
    for i, article in enumerate(articles[:3], 1):  # Afficher les 3 premiers
        print(f"   Article {i}: {article.get('article_num')} ({len(article.get('full_text', ''))} caractères)")

# ============================================================================
# ÉTAPE 3: Génération du débat (Pipeline 3)
# ============================================================================
print(f"\n" + "="*80)
print("ÉTAPE 3: Génération du débat juridique contradictoire (Pipeline 3)")
print("="*80)

print(f"\n🚀 Appel du Pipeline 3...")

response_3 = requests.post(
    PIPELINE_3_URL,
    json={
        "question": test_question,
        "articles": articles
    },
    headers={"Authorization": f"EndpointToken {PIPELINE_3_TOKEN}"},
)

if not response_3.ok:
    print(f"\n❌ ERREUR Pipeline 3: {response_3.status_code}")
    print(response_3.text)
    exit(1)

result_3 = response_3.json()
print(f"\n✅ Pipeline 3 terminé !")

# Extraire le débat
debate = result_3["outputs"]["debate"]["value"]

print(f"\n📊 Débat généré:")
print(f"\n   📍 ROUND 1:")
print(f"      ✅ THÈSE:")
print(f"         {debate['round_1']['these'][:200]}...")
print(f"\n      ❌ ANTITHÈSE:")
print(f"         {debate['round_1']['antithese'][:200]}...")

print(f"\n   📍 ROUND 2:")
print(f"      ✅ THÈSE (répond à antithèse 1):")
print(f"         {debate['round_2']['these'][:200]}...")
print(f"\n      ❌ ANTITHÈSE (répond à thèse 1):")
print(f"         {debate['round_2']['antithese'][:200]}...")

print(f"\n   🎯 SYNTHÈSE:")
print(f"      {debate['synthese'][:300]}...")

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
print(f"\n" + "="*80)
print("RÉSUMÉ DU FLUX COMPLET")
print("="*80)
print(f"\n✅ Question posée: {test_question}")
print(f"✅ Codes identifiés: {codes}")
print(f"✅ Concepts extraits: {concepts}")
print(f"✅ Articles trouvés: {len(articles)}")
print(f"✅ Débat généré: Round 1 + Round 2 + Synthèse")
print(f"\n🎉 Flux complet Pipeline 1 → 2 → 3 fonctionnel !")
