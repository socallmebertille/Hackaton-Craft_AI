"""
Service Légifrance pour la recherche de textes juridiques - Version corrigée
Basé sur l'exemple fonctionnel
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class LegifranceService:
    """Service pour interagir avec l'API Légifrance"""

    def __init__(self):
        """Initialise le client Légifrance"""
        self.client_id = os.getenv("MIBS_LEGIFRANCE_CLIENT_ID")
        self.client_secret = os.getenv("MIBS_LEGIFRANCE_CLIENT_SECRET")
        self.token_url = os.getenv("MIBS_LEGIFRANCE_TOKEN_URL")
        self.api_url = os.getenv("MIBS_LEGIFRANCE_API_URL")

        if not all([self.client_id, self.client_secret, self.token_url, self.api_url]):
            raise ValueError("Variables d'environnement Légifrance manquantes")

        self.access_token = None
        self.token_expires_at = None

        print(f"[LegifranceService] Initialisé")

    def _get_access_token(self) -> str:
        """
        Obtient un token d'accès OAuth2

        Returns:
            str: Token d'accès
        """
        # Vérifier si le token est encore valide
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        print("[LegifranceService] Récupération d'un nouveau token OAuth2...")

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid"
        }

        response = requests.post(self.token_url, data=payload)
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        # Token valide pendant 1 heure, on enlève 5 minutes de marge
        self.token_expires_at = datetime.now() + timedelta(seconds=data.get("expires_in", 3600) - 300)

        print("[LegifranceService] Token OAuth2 obtenu avec succès")
        return self.access_token

    def search_codes(
        self,
        keywords: List[str],
        codes: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans les codes (Code civil, Code pénal, etc.)

        Args:
            keywords: Liste de mots-clés
            codes: Liste de codes spécifiques (ex: ["Code civil"])
            max_results: Nombre maximum de résultats

        Returns:
            Liste de résultats
        """
        token = self._get_access_token()

        print(f"[LegifranceService] Recherche codes avec: {keywords}")
        
        # Construire les critères de recherche
        criteres = []
        for keyword in keywords[:3]:  # Limiter à 3 mots-clés principaux
            criteres.append({
                "typeRecherche": "UN_DES_MOTS",
                "valeur": keyword,
                "operateur": "ET"
            })

        # Construire les filtres
        filtres = []
        if codes:
            filtres.append({
                "facette": "NOM_CODE",
                "valeurs": codes
            })

        payload = {
            "fond": "CODE_DATE",
            "recherche": {
                "champs": [{
                    "typeChamp": "ALL",
                    "criteres": criteres,
                    "operateur": "ET"
                }],
                "filtres": filtres,
                "pageNumber": 1,
                "pageSize": 100,  # Get more results for better deduplication
                "operateur": "ET",
                "sort": "PERTINENCE",
                "typePagination": "DEFAUT"
            }
        }

        try:
            print(f"[LegifranceService] Payload codes:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

            response = requests.post(
                f"{self.api_url}/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            results = []
            articles_by_num = {}  # Déduplication

            for result in data.get("results", [])[:max_results]:
                code_title = "Code inconnu"
                if result.get("titles"):
                    code_title = result["titles"][0].get("title", "Code inconnu")

                for section in result.get("sections", []):
                    for extract in section.get("extracts", []):
                        article_num = extract.get("num", extract.get("title", ""))
                        article_id = extract.get("id", "")
                        text_values = extract.get("values", [])
                        text_preview = " ".join(text_values)[:300] if text_values else ""

                        if article_num and article_num not in articles_by_num:
                            articles_by_num[article_num] = {
                                "type": "CODE",
                                "code_title": code_title,
                                "article_id": article_id,
                                "article_num": article_num,
                                "text_preview": text_preview,
                                "date_version": extract.get("dateVersion", ""),
                                "legal_status": extract.get("legalStatus", "")
                            }

            results = list(articles_by_num.values())
            print(f"[LegifranceService] {len(results)} codes trouvés")
            return results

        except Exception as e:
            print(f"[LegifranceService] Erreur recherche codes: {e}")
            return []

    def search_jurisprudence(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans la jurisprudence

        Args:
            keywords: Liste de mots-clés
            max_results: Nombre maximum de résultats

        Returns:
            Liste de résultats
        """
        token = self._get_access_token()

        search_query = " ".join(keywords)
        print(f"[LegifranceService] Recherche jurisprudence avec: {search_query}")

        payload = {
            "fond": "JURI",
            "recherche": {
                "champs": [{
                    "criteres": [{
                        "valeur": search_query,
                        "operateur": "ET",
                        "typeRecherche": "UN_DES_MOTS"
                    }],
                    "operateur": "ET",
                    "typeChamp": "ALL"
                }],
                "fromAdvancedRecherche": False,
                "pageSize": max_results,
                "operateur": "ET",
                "typePagination": "DEFAUT",
                "pageNumber": 1,
                "sort": "PERTINENCE",
                "secondSort": "DATE_DESC"
            }
        }

        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            results = []
            for result in data.get("results", [])[:max_results]:
                decision_id = result.get("id", "")
                titles = result.get("titles", [])
                decision_title = titles[0].get("title", "Décision") if titles else "Décision"

                # Extraire les extraits
                extracts_text = []
                for section in result.get("sections", [])[:2]:
                    for extract in section.get("extracts", [])[:2]:
                        values = extract.get("values", [])
                        if values:
                            extracts_text.append(" ".join(values)[:200])

                text_preview = " [...] ".join(extracts_text) if extracts_text else ""

                results.append({
                    "type": "JURISPRUDENCE",
                    "decision_id": decision_id,
                    "title": decision_title,
                    "text_preview": text_preview,
                    "date": result.get("dateDecision", ""),
                    "juridiction": result.get("juridiction", "")
                })

            print(f"[LegifranceService] {len(results)} jurisprudences trouvées")
            return results

        except Exception as e:
            print(f"[LegifranceService] Erreur recherche jurisprudence: {e}")
            return []

    def search_all(
        self,
        keywords: List[str],
        codes: Optional[List[str]] = None,
        max_codes: int = 10,
        max_jurisprudence: int = 10
    ) -> Dict[str, Any]:
        """
        Recherche dans tous les types de documents

        Args:
            keywords: Liste de mots-clés
            codes: Liste de codes spécifiques
            max_codes: Nombre max de codes
            max_jurisprudence: Nombre max de jurisprudences

        Returns:
            Dictionnaire avec codes et jurisprudence
        """
        codes_results = self.search_codes(keywords, codes, max_codes)
        juris_results = self.search_jurisprudence(keywords, max_jurisprudence)

        return {
            "codes": codes_results,
            "jurisprudence": juris_results,
            "total_results": len(codes_results) + len(juris_results),
            "keywords_used": keywords
        }


# Pour tester localement
if __name__ == "__main__":
    service = LegifranceService()

    print("\n=== Test 1: Recherche PACS ===")
    results = service.search_all(
        keywords=["pacte civil de solidarité", "dissolution"],
        codes=["Code civil"],
        max_codes=3,
        max_jurisprudence=3
    )

    print(f"\nCodes trouvés: {len(results['codes'])}")
    print(f"Jurisprudences trouvées: {len(results['jurisprudence'])}")

    if results['codes']:
        print(f"\nPremier code: {results['codes'][0]['article_num']}")
        print(f"Preview: {results['codes'][0]['text_preview'][:100]}...")

    if results['jurisprudence']:
        print(f"\nPremière jurisprudence: {results['jurisprudence'][0]['title']}")
        print(f"\n2 jurisprudence: {results['jurisprudence'][1]['title']}")
