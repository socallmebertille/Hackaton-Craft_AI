"""
Service Mistral pour générer des débats juridiques contradictoires

Ce service utilise Mistral AI pour analyser des textes juridiques
et générer un débat POUR/CONTRE avec synthèse.
"""

import os
from typing import Dict, List
from mistralai import Mistral


class MistralDebateService:
    """Service pour générer des débats juridiques avec Mistral AI"""

    def __init__(self):
        """
        Initialise le client Mistral AI
        """
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY doit être définie")

        self.client = Mistral(api_key=api_key)
        print("[MistralDebateService] ✅ Client Mistral initialisé")

    def generate_debate(self, question: str, articles: List[Dict]) -> Dict:
        """
        Génère un débat juridique contradictoire à partir d'une question
        et des articles de loi pertinents

        Args:
            question (str): Question juridique posée par l'utilisateur
            articles (List[Dict]): Liste des articles avec leur texte complet
                [
                    {
                        "article_num": "515-7",
                        "section_title": "Chapitre...",
                        "full_text": "Le texte complet de l'article..."
                    }
                ]

        Returns:
            Dict: {
                "question": "...",
                "these": {
                    "titre": "Arguments en faveur",
                    "arguments": ["arg1", "arg2", "arg3"]
                },
                "antithese": {
                    "titre": "Arguments opposés",
                    "arguments": ["arg1", "arg2", "arg3"]
                },
                "synthese": "Analyse équilibrée et recommandations..."
            }
        """
        print(f"\n[MistralDebateService] Génération du débat juridique...")
        print(f"[MistralDebateService] Question: {question}")
        print(f"[MistralDebateService] Nombre d'articles: {len(articles)}")

        # Construire le contexte avec les articles
        articles_context = self._build_articles_context(articles)

        # Construire le prompt pour Mistral
        prompt = f"""Tu es un expert juridique français. Tu dois analyser une question juridique et générer un débat contradictoire en 2 ROUNDS basé sur les textes de loi fournis.

**Question posée:**
{question}

**Textes juridiques pertinents:**
{articles_context}

**Ta mission:**
Génère un débat juridique contradictoire EN 2 ROUNDS au format JSON strict avec la structure suivante:

{{
  "round_1": {{
    "these": "Argument principal en faveur d'une position juridique (cite l'article)",
    "antithese": "Argument principal contre cette position juridique (cite l'article)"
  }},
  "round_2": {{
    "these": "Réfute l'ANTITHÈSE du round 1 pour défendre la position initiale (cite l'article)",
    "antithese": "Réfute la THÈSE du round 1 pour renforcer la position contraire (cite l'article)"
  }},
  "synthese": "Une synthèse équilibrée analysant les 2 rounds, citant les articles clés, et fournissant une recommandation juridique nuancée. Cette synthèse doit faire au moins 3-4 phrases."
}}

**Instructions importantes:**
- ROUND 1: Présente un argument initial pour chaque position
- ROUND 2: Chaque côté RÉPOND à l'argument adverse du round 1
  * La thèse du round 2 répond à l'antithèse du round 1
  * L'antithèse du round 2 répond à la thèse du round 1
- Chaque argument doit CITER explicitement l'article de loi concerné (ex: "Selon l'article 515-7...")
- Base-toi UNIQUEMENT sur les textes fournis, n'invente rien
- La synthèse doit analyser l'ensemble des 2 rounds et donner une analyse juridique solide
- Réponds UNIQUEMENT en JSON, sans texte supplémentaire
"""

        try:
            # Appel à Mistral avec JSON mode
            response = self.client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Créativité modérée pour analyse juridique
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            # Extraire le contenu JSON
            import json
            debate_data = json.loads(response.choices[0].message.content)

            print(f"[MistralDebateService] ✅ Débat en 2 rounds généré avec succès")
            print(f"[MistralDebateService]   Round 1 - Thèse: {len(debate_data.get('round_1', {}).get('these', ''))} caractères")
            print(f"[MistralDebateService]   Round 1 - Antithèse: {len(debate_data.get('round_1', {}).get('antithese', ''))} caractères")
            print(f"[MistralDebateService]   Round 2 - Thèse: {len(debate_data.get('round_2', {}).get('these', ''))} caractères")
            print(f"[MistralDebateService]   Round 2 - Antithèse: {len(debate_data.get('round_2', {}).get('antithese', ''))} caractères")
            print(f"[MistralDebateService]   Synthèse: {len(debate_data.get('synthese', ''))} caractères")

            return {
                "question": question,
                "round_1": debate_data.get("round_1", {}),
                "round_2": debate_data.get("round_2", {}),
                "synthese": debate_data.get("synthese", ""),
                "articles_used": [
                    {
                        "article_num": art.get("article_num", ""),
                        "section_title": art.get("section_title", "")
                    }
                    for art in articles
                ]
            }

        except Exception as e:
            print(f"[MistralDebateService] ❌ Erreur: {e}")
            return {
                "question": question,
                "error": str(e),
                "round_1": {},
                "round_2": {},
                "synthese": ""
            }

    def _build_articles_context(self, articles: List[Dict]) -> str:
        """
        Construit le contexte textuel à partir des articles

        Args:
            articles (List[Dict]): Liste des articles

        Returns:
            str: Contexte formaté pour le prompt
        """
        context_parts = []

        for i, article in enumerate(articles, 1):
            article_num = article.get("article_num", "Inconnu")
            section = article.get("section_title", "")
            text = article.get("full_text", "")

            context_parts.append(f"""
Article {article_num}
Section: {section}
Texte:
{text}
""")

        return "\n---\n".join(context_parts)


# Fonction standalone pour faciliter l'import dans les pipelines
def generate_legal_debate(question: str, articles: List[Dict]) -> Dict:
    """
    Fonction utilitaire pour générer un débat juridique

    Args:
        question (str): Question juridique
        articles (List[Dict]): Articles avec texte complet

    Returns:
        Dict: Débat généré (thèse, antithèse, synthèse)
    """
    service = MistralDebateService()
    return service.generate_debate(question, articles)
