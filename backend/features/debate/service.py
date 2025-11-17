"""
Services métier pour la feature Debate
Utilise les 3 pipelines CraftAI séquentiels pour générer des débats juridiques
"""
from datetime import datetime
import os
import requests
from .storage import debates_storage


# ========== CONFIGURATION CRAFT AI ==========
CRAFTAI_PIPELINE_1_URL = os.getenv("CRAFTAI_PIPELINE_1_URL")
CRAFTAI_PIPELINE_1_TOKEN = os.getenv("CRAFTAI_PIPELINE_1_TOKEN")
CRAFTAI_PIPELINE_2_URL = os.getenv("CRAFTAI_PIPELINE_2_URL")
CRAFTAI_PIPELINE_2_TOKEN = os.getenv("CRAFTAI_PIPELINE_2_TOKEN")
CRAFTAI_PIPELINE_3_URL = os.getenv("CRAFTAI_PIPELINE_3_URL")
CRAFTAI_PIPELINE_3_TOKEN = os.getenv("CRAFTAI_PIPELINE_3_TOKEN")


def run_debate_background(debate_id: str, question: str):
    """
    Exécute le pipeline de débat en arrière-plan via les 3 pipelines CraftAI

    Cette fonction orchestre les 3 pipelines CraftAI en séquence:
    Pipeline 1 → Extraction des concepts juridiques
    Pipeline 2 → Recherche des articles sur Légifrance
    Pipeline 3 → Génération du débat contradictoire

    Le pipeline complet prend typiquement 30-90 secondes.

    Workflow:
    1. Pipeline 1: Extrait codes, concepts et nature_filter de la question
    2. Pipeline 2: Recherche les articles pertinents sur Légifrance
    3. Pipeline 3: Génère le débat (2 rounds: thèse/antithèse + synthèse)
    4. Met à jour debates_storage avec les résultats
    5. Gère les erreurs éventuelles

    Args:
        debate_id (str): UUID du débat (clé dans debates_storage)
        question (str): Question juridique à traiter

    Side effects:
        - Modifie debates_storage[debate_id] avec les résultats
        - Affiche des logs via print() pour le monitoring
        - En cas de succès: status="completed", résultats remplis
        - En cas d'erreur: status="error", champ error rempli
    """
    try:
        debates_storage[debate_id]["status"] = "processing"
        debates_storage[debate_id]["progress"] = "Extraction des concepts juridiques..."

        # ========== PIPELINE 1: Extraction des concepts ==========
        print(f"[Debate {debate_id}] Pipeline 1: Extraction des concepts...")
        response_1 = requests.post(
            CRAFTAI_PIPELINE_1_URL,
            json={"question": question},
            headers={"Authorization": f"EndpointToken {CRAFTAI_PIPELINE_1_TOKEN}"},
            timeout=60
        )

        if not response_1.ok:
            raise Exception(f"Pipeline 1 failed: {response_1.status_code} - {response_1.text}")

        result_1 = response_1.json()
        extraction_data = result_1["outputs"]["result"]["value"]
        codes = extraction_data["search_params"]["codes"]
        concepts = extraction_data["search_params"]["concepts"]
        nature_filter = extraction_data["search_params"]["nature_filter"]

        debates_storage[debate_id]["legal_context"] = {
            "codes": codes,
            "concepts": concepts,
            "nature_filter": nature_filter
        }

        # ========== PIPELINE 2: Recherche Legifrance ==========
        debates_storage[debate_id]["progress"] = "Recherche des textes juridiques..."
        print(f"[Debate {debate_id}] Pipeline 2: Recherche Legifrance...")

        response_2 = requests.post(
            CRAFTAI_PIPELINE_2_URL,
            json={
                "codes": codes,
                "concepts": concepts,
                "nature_filter": nature_filter
            },
            headers={"Authorization": f"EndpointToken {CRAFTAI_PIPELINE_2_TOKEN}"},
            timeout=60
        )

        if not response_2.ok:
            raise Exception(f"Pipeline 2 failed: {response_2.status_code} - {response_2.text}")

        result_2 = response_2.json()
        articles = result_2["outputs"]["articles"]["value"]

        debates_storage[debate_id]["legal_context"]["articles_count"] = len(articles)

        # ========== PIPELINE 3: Génération du débat ==========
        debates_storage[debate_id]["progress"] = "Génération du débat contradictoire..."
        print(f"[Debate {debate_id}] Pipeline 3: Génération du débat...")

        response_3 = requests.post(
            CRAFTAI_PIPELINE_3_URL,
            json={
                "question": question,
                "articles": articles
            },
            headers={"Authorization": f"EndpointToken {CRAFTAI_PIPELINE_3_TOKEN}"},
            timeout=120
        )

        if not response_3.ok:
            raise Exception(f"Pipeline 3 failed: {response_3.status_code} - {response_3.text}")

        result_3 = response_3.json()
        debate = result_3["outputs"]["debate"]["value"]

        # Formater le débat pour le frontend
        debate_rounds = [
            {"position": "pour", "round": 1, "argument": debate["round_1"]["these"]},
            {"position": "contre", "round": 1, "argument": debate["round_1"]["antithese"]},
            {"position": "pour", "round": 2, "argument": debate["round_2"]["these"]},
            {"position": "contre", "round": 2, "argument": debate["round_2"]["antithese"]},
        ]

        debates_storage[debate_id]["debate_rounds"] = debate_rounds
        debates_storage[debate_id]["summary"] = debate["synthese"]
        debates_storage[debate_id]["status"] = "completed"
        debates_storage[debate_id]["progress"] = "Débat terminé"
        debates_storage[debate_id]["completed_at"] = datetime.now().isoformat()

        print(f"[Debate {debate_id}] ✅ Débat complété avec succès!")

    except Exception as e:
        print(f"[Debate {debate_id}] ❌ Erreur: {str(e)}")
        debates_storage[debate_id]["status"] = "error"
        debates_storage[debate_id]["error"] = str(e)
        debates_storage[debate_id]["progress"] = f"Erreur: {str(e)}"
