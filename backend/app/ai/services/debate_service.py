"""
Service de débat contradictoire avec Mistral AI

Ce service génère un débat structuré en 4 rounds (2 pour, 2 contre) + synthèse
en se basant UNIQUEMENT sur les sources juridiques fournies.
"""

import os
import json
from typing import Dict, List, Any
from mistralai import Mistral


class DebateService:
    """Service pour générer des débats juridiques contradictoires"""

    def __init__(self):
        """Initialise le service Mistral"""
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = os.getenv("MISTRAL_MODEL_SMALL", "mistral-small-latest")

        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY n'est pas définie")

        self.client = Mistral(api_key=self.api_key)

    def generate_debate(self, question: str, legal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un débat contradictoire basé sur les sources juridiques

        Args:
            question: Question juridique de l'utilisateur
            legal_data: Données juridiques de P1 (codes + jurisprudence)

        Returns:
            dict: Débat structuré avec pour/contre rounds + synthèse
        """
        print(f"[DebateService] Génération d'un débat pour: {question[:100]}...")

        # Préparer les sources juridiques
        sources_text = self._format_sources(legal_data)

        # Générer le débat
        debate_result = self._call_mistral_debate(question, sources_text)

        return debate_result

    def _format_sources(self, legal_data: Dict[str, Any]) -> str:
        """
        Formate les sources juridiques pour le prompt

        Args:
            legal_data: Données de P1

        Returns:
            str: Sources formatées
        """
        sources_parts = []

        # Articles de code
        codes = legal_data.get("codes", [])
        if codes:
            sources_parts.append("=== ARTICLES DE CODE ===\n")
            for i, code in enumerate(codes, 1):
                article_num = code.get("article_num", "N/A")
                code_title = code.get("code_title", "Code").replace("<mark>", "").replace("</mark>", "")
                text = code.get("text_preview", "").replace("<mark>", "").replace("</mark>", "").replace("[...]", "")
                article_id = code.get("article_id", "")

                sources_parts.append(f"\n[CODE {i}] {code_title} - Article {article_num}")
                sources_parts.append(f"Référence: {article_id}")
                sources_parts.append(f"Texte: {text.strip()}\n")

        # Jurisprudence
        jurisprudence = legal_data.get("jurisprudence", [])
        if jurisprudence:
            sources_parts.append("\n=== JURISPRUDENCE ===\n")
            for i, juris in enumerate(jurisprudence, 1):
                title = juris.get("title", "").replace("<mark>", "").replace("</mark>", "")
                text = juris.get("text_preview", "").replace("<mark>", "").replace("</mark>", "").replace("[...]", "")

                sources_parts.append(f"\n[JURIS {i}] {title}")
                sources_parts.append(f"Extrait: {text.strip()}\n")

        return "\n".join(sources_parts)

    def _call_mistral_debate(self, question: str, sources: str) -> Dict[str, Any]:
        """
        Appelle Mistral pour générer le débat

        Args:
            question: Question de l'utilisateur
            sources: Sources juridiques formatées

        Returns:
            dict: Débat structuré
        """
        system_prompt = """Tu es un expert juridique spécialisé dans les débats contradictoires.

RÈGLES STRICTES:
1. AUCUN emoji dans ta réponse
2. Tu dois UNIQUEMENT utiliser les sources juridiques fournies
3. JAMAIS de connaissances externes ou générales
4. Chaque argument doit citer précisément la référence juridique exacte (ex: "l'article 515-7 du Code civil", "Cour de cassation, 23 janvier 2014")
5. Si les sources ne permettent pas d'argumenter un point, ne l'invente pas
6. 2-3 arguments maximum par round
7. Cite TOUJOURS les références complètes : "l'article X du Code Y" ou "Cour de cassation, date"
8. Utilise POUR et CONTRE comme titres de positions (pas "Position A" ou "Position B")

STRUCTURE DU DÉBAT:
1. Identifie les deux positions possibles: POUR et CONTRE
2. Round 1 POUR: 2-3 arguments en faveur
3. Round 1 CONTRE: 2-3 arguments contre
4. Round 2 POUR: Réfutation + renforcement avec 2-3 nouveaux arguments
5. Round 2 CONTRE: Réfutation + renforcement avec 2-3 nouveaux arguments
6. SYNTHÈSE: Vision équilibrée des deux positions

FORMAT DE RÉPONSE (JSON strict):
{
  "position_pour": "Description claire de ce qui est argumenté POUR (sans emoji, sans titre)",
  "position_contre": "Description claire de ce qui est argumenté CONTRE (sans emoji, sans titre)",
  "pour_round_1": "Arguments POUR avec citations exactes (Article X du Code Y). Format markdown accepté.",
  "contre_round_1": "Arguments CONTRE avec citations exactes. Format markdown accepté.",
  "pour_round_2": "Réfutation et nouveaux arguments POUR avec citations exactes. Format markdown accepté.",
  "contre_round_2": "Réfutation et nouveaux arguments CONTRE avec citations exactes. Format markdown accepté.",
  "synthese": "Vision équilibrée finale sans emoji",
  "sources_citees": ["Article 515-7 du Code civil", "Cour de cassation, 23 janvier 2014", ...]
}"""

        user_prompt = f"""QUESTION: {question}

SOURCES JURIDIQUES DISPONIBLES:
{sources}

Génère un débat contradictoire en suivant strictement les règles.
Retourne UNIQUEMENT le JSON, sans texte avant ou après."""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            # Extraire et parser la réponse JSON
            response_text = response.choices[0].message.content
            debate_data = json.loads(response_text)

            print(f"[DebateService] Débat généré avec succès")
            print(f"  Position POUR: {debate_data.get('position_pour', '')[:50]}...")
            print(f"  Position CONTRE: {debate_data.get('position_contre', '')[:50]}...")
            print(f"  Sources citées: {len(debate_data.get('sources_citees', []))}")

            return debate_data

        except json.JSONDecodeError as e:
            print(f"[DebateService] Erreur JSON: {e}")
            print(f"  Réponse brute: {response_text[:200]}...")
            raise ValueError(f"Erreur de parsing JSON du débat: {e}")

        except Exception as e:
            print(f"[DebateService] Erreur lors de l'appel Mistral: {e}")
            raise
