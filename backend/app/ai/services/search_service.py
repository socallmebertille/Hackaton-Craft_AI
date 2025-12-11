"""
Service de recherche itérative pour Légifrance
Stratégie : Privilégier la pertinence sur la quantité
"""

from typing import Dict, List, Any
from .mistral_service import MistralService
from .legifrance_service import LegifranceService


class SearchService:
    """Service de recherche itérative intelligente"""

    def __init__(self):
        self.mistral = MistralService()
        self.legifrance = LegifranceService()

        # Limites strictes pour privilégier la qualité
        self.MAX_CODES = 5
        self.MAX_JURISPRUDENCE = 5

    def search_legal_documents(
        self,
        message: str,
        intention: str
    ) -> Dict[str, Any]:
        """
        Recherche itérative de documents juridiques

        Stratégie :
        1. Tentative 1 : Recherche précise avec tous les mots-clés
        2. Si 0 résultat : Reformuler avec Mistral (synonymes juridiques)
        3. Si toujours 0 : Élargir aux 2 concepts principaux seulement

        Args:
            message: Question de l'utilisateur
            intention: DEBAT ou CITATIONS

        Returns:
            dict: {
                "codes": [...],  # Max 5
                "jurisprudence": [...],  # Max 5
                "keywords_used": [...],
                "total_codes": int,
                "total_jurisprudence": int,
                "search_strategy": "precise" | "reformulated" | "broad"
            }
        """
        print(f"[SearchService] Recherche pour: {message[:100]}...")

        # Étape 1 : Extraire les mots-clés initiaux
        extraction = self.mistral.extract_keywords(message, intention)
        keywords = extraction.get("keywords", [])
        codes = extraction.get("codes", [])

        if not keywords:
            print("[SearchService] Aucun mot-clé extrait, abandon")
            return self._empty_result()

        # Tentative 1 : Recherche précise
        print(f"[SearchService] Tentative 1 - Recherche précise avec: {keywords}")
        result = self._search_attempt(keywords, codes)

        if result["total_codes"] > 0 or result["total_jurisprudence"] > 0:
            print(f"[SearchService] ✅ Succès tentative 1 : {result['total_codes']} codes, {result['total_jurisprudence']} juris")
            result["search_strategy"] = "precise"
            result["keywords_used"] = keywords
            return result

        # Tentative 2 : Reformuler avec Mistral si 0 résultat
        print("[SearchService] 0 résultat, tentative 2 - Reformulation...")
        reformulated = self._reformulate_keywords(message, keywords)

        if reformulated and reformulated != keywords:
            print(f"[SearchService] Nouveaux termes: {reformulated}")
            result = self._search_attempt(reformulated, codes)

            if result["total_codes"] > 0 or result["total_jurisprudence"] > 0:
                print(f"[SearchService] ✅ Succès tentative 2 : {result['total_codes']} codes, {result['total_jurisprudence']} juris")
                result["search_strategy"] = "reformulated"
                result["keywords_used"] = reformulated
                return result

        # Tentative 3 : Élargir aux 2 concepts principaux seulement
        if len(keywords) > 2:
            print("[SearchService] Tentative 3 - Élargissement aux 2 concepts principaux...")
            broad_keywords = keywords[:2]
            print(f"[SearchService] Recherche avec: {broad_keywords}")
            result = self._search_attempt(broad_keywords, codes)

            if result["total_codes"] > 0 or result["total_jurisprudence"] > 0:
                print(f"[SearchService] ✅ Succès tentative 3 : {result['total_codes']} codes, {result['total_jurisprudence']} juris")
                result["search_strategy"] = "broad"
                result["keywords_used"] = broad_keywords
                return result

        # Échec : Aucun résultat trouvé
        print("[SearchService] ❌ Aucun résultat trouvé après 3 tentatives")
        empty = self._empty_result()
        empty["keywords_used"] = keywords
        empty["search_strategy"] = "failed"
        return empty

    def _search_attempt(
        self,
        keywords: List[str],
        codes: List[str]
    ) -> Dict[str, Any]:
        """
        Effectue une tentative de recherche

        Args:
            keywords: Liste de mots-clés
            codes: Liste de codes suggérés (peut être vide)

        Returns:
            dict: Résultats de recherche
        """
        # Rechercher dans Légifrance
        result = self.legifrance.search_all(
            keywords=keywords,
            codes=codes if codes else None,
            max_codes=self.MAX_CODES,
            max_jurisprudence=self.MAX_JURISPRUDENCE
        )

        return {
            "codes": result.get("codes", []),
            "jurisprudence": result.get("jurisprudence", []),
            "total_codes": len(result.get("codes", [])),
            "total_jurisprudence": len(result.get("jurisprudence", []))
        }

    def _reformulate_keywords(
        self,
        original_message: str,
        original_keywords: List[str]
    ) -> List[str]:
        """
        Demande à Mistral de reformuler les mots-clés avec des synonymes juridiques

        Args:
            original_message: Question originale
            original_keywords: Mots-clés qui n'ont pas donné de résultats

        Returns:
            Liste de nouveaux mots-clés
        """
        print(f"[SearchService] Reformulation des mots-clés: {original_keywords}")

        system_prompt = """Tu es un expert juridique. Les mots-clés précédents n'ont donné aucun résultat dans Légifrance.

Propose des SYNONYMES ou TERMES ALTERNATIFS juridiques qui pourraient mieux fonctionner.

Exemples :
- "rupture PACS" → "dissolution pacte civil de solidarité"
- "licenciement abusif" → "rupture contrat travail sans cause réelle et sérieuse"
- "divorce" → "dissolution mariage"

Réponds UNIQUEMENT avec un JSON :
{
    "keywords": ["nouveau terme 1", "nouveau terme 2"],  // 2-4 termes max
    "reasoning": "Explication rapide"
}"""

        user_prompt = f"""Question originale : "{original_message}"
Mots-clés qui ont échoué : {original_keywords}

Propose des termes juridiques alternatifs."""

        try:
            response = self.mistral.client.chat.complete(
                model=self.mistral.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            content = response.choices[0].message.content
            result = json.loads(content)

            new_keywords = result.get("keywords", [])
            print(f"[SearchService] Reformulation suggérée: {new_keywords}")

            return new_keywords if new_keywords else original_keywords

        except Exception as e:
            print(f"[SearchService] Erreur reformulation: {e}")
            return original_keywords

    def _empty_result(self) -> Dict[str, Any]:
        """Retourne un résultat vide"""
        return {
            "codes": [],
            "jurisprudence": [],
            "total_codes": 0,
            "total_jurisprudence": 0,
            "keywords_used": [],
            "search_strategy": "none"
        }


# Test local
if __name__ == "__main__":
    service = SearchService()

    # Test 1 : Question sur le PACS
    print("\n" + "="*80)
    print("TEST 1 : Question PACS")
    print("="*80)
    result = service.search_legal_documents(
        message="Quelles sont les conséquences juridiques de la dissolution d'un PACS ?",
        intention="DEBAT"
    )
    print(f"\n✅ Résultats:")
    print(f"  - Codes: {result['total_codes']}")
    print(f"  - Jurisprudences: {result['total_jurisprudence']}")
    print(f"  - Stratégie: {result['search_strategy']}")
    print(f"  - Mots-clés utilisés: {result['keywords_used']}")
