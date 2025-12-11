"""
Service de génération d'explications concises pour les citations juridiques

Ce service prend les sources juridiques (codes + jurisprudence) et génère
une explication brève et claire pour chaque citation.
"""

import os
import json
from typing import Dict, List, Any
from mistralai import Mistral


class CitationService:
    """Service pour générer des explications concises de citations juridiques"""

    def __init__(self):
        """Initialise le service Mistral"""
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = os.getenv("MISTRAL_MODEL_SMALL", "mistral-small-latest")

        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY n'est pas définie")

        self.client = Mistral(api_key=self.api_key)

    def generate_citations(self, question: str, legal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère des explications concises pour chaque citation juridique

        Args:
            question: Question juridique de l'utilisateur
            legal_data: Données juridiques de P1 (codes + jurisprudence)

        Returns:
            dict: Citations avec explications brèves
        """
        print(f"[CitationService] Génération des citations pour: {question[:100]}...")

        codes = legal_data.get("codes", [])
        jurisprudence = legal_data.get("jurisprudence", [])

        citations_result = {
            "question": question,
            "codes_expliques": [],
            "jurisprudence_expliquee": [],
            "total_codes": len(codes),
            "total_jurisprudence": len(jurisprudence)
        }

        # Générer les explications pour les codes
        if codes:
            citations_result["codes_expliques"] = self._explain_codes(codes, question)

        # Générer les explications pour la jurisprudence
        if jurisprudence:
            citations_result["jurisprudence_expliquee"] = self._explain_jurisprudence(jurisprudence, question)

        print(f"[CitationService] ✅ Citations générées avec succès")
        print(f"  Codes expliqués: {len(citations_result['codes_expliques'])}")
        print(f"  Jurisprudences expliquées: {len(citations_result['jurisprudence_expliquee'])}")

        return citations_result

    def _explain_codes(self, codes: List[Dict[str, Any]], question: str) -> List[Dict[str, str]]:
        """
        Génère des explications concises pour les articles de code

        Args:
            codes: Liste des articles de code
            question: Question de l'utilisateur pour le contexte

        Returns:
            list: Liste avec référence + explication brève
        """
        if not codes:
            return []

        # Préparer les codes pour le prompt
        codes_text = []
        for i, code in enumerate(codes, 1):
            article_num = code.get("article_num", "N/A")
            code_title = code.get("code_title", "Code").replace("<mark>", "").replace("</mark>", "")
            text = code.get("text_preview", "").replace("<mark>", "").replace("</mark>", "").replace("[...]", "")

            codes_text.append(f"[{i}] {code_title} - Article {article_num}")
            codes_text.append(f"Texte: {text.strip()}")
            codes_text.append("")

        system_prompt = """Tu es un expert juridique qui explique des articles de loi de manière concise.

RÈGLES STRICTES:
1. Une seule phrase courte par explication (15-25 mots maximum)
2. Langage clair et accessible
3. Résume l'essentiel de l'article en lien avec la question
4. Pas de citations du texte, juste l'explication
5. Format JSON strict

EXEMPLE:
{
  "explanations": [
    {
      "reference": "Article 515-7 du Code civil",
      "explanation": "Prévoit la dissolution du PACS par déclaration conjointe ou unilatérale des partenaires."
    }
  ]
}"""

        user_prompt = f"""QUESTION DE L'UTILISATEUR: {question}

ARTICLES À EXPLIQUER:
{chr(10).join(codes_text)}

Pour chaque article, fournis une explication brève et claire en JSON."""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            result = json.loads(response_text)

            print(f"[CitationService] Codes expliqués: {len(result.get('explanations', []))}")
            return result.get("explanations", [])

        except json.JSONDecodeError as e:
            print(f"[CitationService] Erreur JSON pour codes: {e}")
            # Fallback: retourner les codes sans explication
            return [
                {
                    "reference": f"{code.get('code_title', 'Code')} - Article {code.get('article_num', 'N/A')}",
                    "explanation": code.get("text_preview", "")[:100] + "..."
                }
                for code in codes
            ]

        except Exception as e:
            print(f"[CitationService] Erreur lors de l'explication des codes: {e}")
            return []

    def _explain_jurisprudence(self, jurisprudence: List[Dict[str, Any]], question: str) -> List[Dict[str, str]]:
        """
        Génère des explications concises pour la jurisprudence

        Args:
            jurisprudence: Liste des décisions de justice
            question: Question de l'utilisateur pour le contexte

        Returns:
            list: Liste avec référence + explication brève
        """
        if not jurisprudence:
            return []

        # Préparer la jurisprudence pour le prompt
        juris_text = []
        for i, juris in enumerate(jurisprudence, 1):
            title = juris.get("title", "").replace("<mark>", "").replace("</mark>", "")
            text = juris.get("text_preview", "").replace("<mark>", "").replace("</mark>", "").replace("[...]", "")

            juris_text.append(f"[{i}] {title}")
            juris_text.append(f"Extrait: {text.strip()}")
            juris_text.append("")

        system_prompt = """Tu es un expert juridique qui explique des décisions de justice de manière concise.

RÈGLES STRICTES:
1. Une seule phrase courte par explication (15-25 mots maximum)
2. Langage clair et accessible
3. Résume le principe juridique établi par l'arrêt
4. Pas de citations du texte, juste l'explication
5. Format JSON strict
6. IMPORTANT: La référence DOIT inclure le numéro de décision (ex: 21-21.185) s'il est présent dans le titre

EXEMPLE:
{
  "explanations": [
    {
      "reference": "Cour de cassation, Chambre civile 1, 27 janvier 2021, 19-26.140",
      "explanation": "Confirme que l'aide matérielle entre partenaires est une obligation fondamentale du PACS."
    }
  ]
}"""

        user_prompt = f"""QUESTION DE L'UTILISATEUR: {question}

JURISPRUDENCE À EXPLIQUER:
{chr(10).join(juris_text)}

Pour chaque décision, fournis une explication brève et claire en JSON."""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            result = json.loads(response_text)

            print(f"[CitationService] Jurisprudences expliquées: {len(result.get('explanations', []))}")
            return result.get("explanations", [])

        except json.JSONDecodeError as e:
            print(f"[CitationService] Erreur JSON pour jurisprudence: {e}")
            # Fallback: retourner la jurisprudence sans explication
            return [
                {
                    "reference": juris.get("title", "Décision de justice"),
                    "explanation": juris.get("text_preview", "")[:100] + "..."
                }
                for juris in jurisprudence
            ]

        except Exception as e:
            print(f"[CitationService] Erreur lors de l'explication de la jurisprudence: {e}")
            return []
