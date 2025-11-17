"""
Service Legifrance pour l'assistant juridique

Ce service utilise l'API Legifrance pour:
1. Rechercher des textes juridiques (codes, lois, jurisprudence)
2. (À venir) Consulter le contenu complet des textes
"""

import os
import json
import requests
from typing import Dict, List


class LegifranceService:
    """Service pour interagir avec l'API Legifrance"""

    def __init__(self):
        """
        Initialise le client Legifrance

        Charge les credentials depuis les variables d'environnement
        """
        self.client_id = os.getenv("MIBS_LEGIFRANCE_CLIENT_ID")
        self.client_secret = os.getenv("MIBS_LEGIFRANCE_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError("MIBS_LEGIFRANCE_CLIENT_ID et MIBS_LEGIFRANCE_CLIENT_SECRET doivent être définis")

        # URLs de l'API sandbox
        self.oauth_url = os.getenv("MIBS_LEGIFRANCE_TOKEN_URL", "https://sandbox-oauth.piste.gouv.fr/api/oauth/token")
        self.api_url = os.getenv("MIBS_LEGIFRANCE_API_URL", "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app")

        # Token d'accès (sera obtenu à la demande)
        self.access_token = None

    def _get_access_token(self) -> str:
        """
        Obtient un token d'accès OAuth2 pour l'API Legifrance

        Returns:
            str: Token d'accès Bearer

        Raises:
            Exception: Si l'authentification échoue
        """
        if self.access_token:
            return self.access_token

        print("[LegifranceService] Authentification OAuth2...")

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid"
        }

        try:
            response = requests.post(self.oauth_url, data=payload)
            response.raise_for_status()

            self.access_token = response.json()["access_token"]
            print("[LegifranceService] ✅ Authentification réussie")

            return self.access_token

        except Exception as e:
            print(f"[LegifranceService] ❌ Erreur authentification: {e}")
            raise Exception(f"Erreur authentification Legifrance: {str(e)}")

    def _map_code_to_fond(self, codes: List[str]) -> str:
        """
        Détermine le fond Legifrance à partir du code juridique

        Args:
            codes (List[str]): Liste des codes juridiques (ex: ["Code civil"])

        Returns:
            str: Fond Legifrance (CODE_DATE, LODA_DATE, JURI, etc.)
        """
        if not codes:
            return "CODE_DATE"  # Par défaut

        code = codes[0].lower()

        # Mapping codes → fonds
        if "code" in code:
            return "CODE_DATE"  # Tous les codes (civil, pénal, travail, etc.)
        elif "loi" in code or "ordonnance" in code:
            return "LODA_DATE"  # Lois et ordonnances
        else:
            return "CODE_DATE"  # Par défaut

    def search(self, search_params: Dict, with_full_text: bool = False, top_n: int = 5) -> Dict:
        """
        Recherche des textes juridiques sur Legifrance

        Args:
            search_params (Dict): Paramètres de recherche issus de Mistral
                {
                    "codes": ["Code civil"],
                    "concepts": ["PACS", "dissolution", "rupture"],
                    "nature_filter": ["CODE"]
                }
            with_full_text (bool): Si True, récupère le texte complet des top_n meilleurs articles
            top_n (int): Nombre d'articles dont on veut le texte complet (défaut: 5)

        Returns:
            Dict: {
                "results": [
                    {
                        "code_title": "Code civil",
                        "nature": "code",
                        "articles": [
                            {
                                "article_id": "LEGIARTI...",
                                "article_num": "515-7",
                                "text_preview": "...",
                                "full_text": "..." (si with_full_text=True)
                            }
                        ]
                    }
                ],
                "total": 42,
                "query": "PACS dissolution rupture"
            }
        """
        codes = search_params.get("codes", [])
        concepts = search_params.get("concepts", [])
        nature_filter = search_params.get("nature_filter", ["CODE"])

        # Stratégie de fallback : essayer d'abord avec tous les concepts,
        # puis avec moins de concepts si on ne trouve pas assez d'articles
        min_articles_wanted = 3

        # Tentative 1 : Tous les concepts
        search_query = " ".join(concepts)

        print(f"[LegifranceService] Recherche: '{search_query}'")
        print(f"[LegifranceService] Codes: {codes}")
        print(f"[LegifranceService] Nature: {nature_filter}")

        # Déterminer le fond
        fond = self._map_code_to_fond(codes)
        print(f"[LegifranceService] Fond sélectionné: {fond}")

        # Payload selon la documentation officielle Legifrance
        # Construction du filtre selon le type de code
        filtres = []

        # Si c'est un code (Code civil, Code pénal, etc.)
        if codes and fond in ["CODE_DATE", "CODE_ETAT"]:
            filtres.append({
                "facette": "TEXT_NOM_CODE" if fond == "CODE_ETAT" else "NOM_CODE",
                "valeurs": codes  # ["Code civil"]
            })

        payload = {
            "fond": fond,
            "recherche": {
                "champs": [{
                    "typeChamp": "ARTICLE",  # Recherche dans les articles
                    "criteres": [{
                        "typeRecherche": "UN_DES_MOTS",  # Au moins un des mots
                        "valeur": search_query,
                        "operateur": "ET"
                    }],
                    "operateur": "ET"
                }],
                "filtres": filtres,
                "pageNumber": 1,
                "pageSize": 100,  # Augmenter pour avoir plus de résultats et trouver plus d'articles uniques
                "operateur": "ET",
                "sort": "PERTINENCE",
                "typePagination": "DEFAUT"
            }
        }

        try:
            # Obtenir le token
            token = self._get_access_token()

            # Appeler l'API
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            url = f"{self.api_url}/search"

            print(f"[LegifranceService] Appel API: POST {url}")

            # Debug: afficher le payload
            print(f"[LegifranceService] Payload envoyé:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

            response = requests.post(url, json=payload, headers=headers)

            # Debug: afficher la réponse brute en cas d'erreur
            if response.status_code >= 400:
                print(f"[LegifranceService] ❌ Status: {response.status_code}")
                print(f"[LegifranceService] ❌ Réponse: {response.text}")

            response.raise_for_status()

            data = response.json()

            # Extraire les résultats
            results = data.get("results", [])
            total = data.get("totalResultNumber", 0)

            print(f"[LegifranceService] ✅ {total} résultats trouvés")

            # Formater les résultats et dédupliquer les articles
            # L'API retourne souvent plusieurs versions temporelles du même texte
            # On garde la version la plus récente de chaque article unique
            # Déduplication par numéro d'article (ex: "515-5-3") car l'ID change entre versions
            articles_by_num = {}  # {article_num: article_data}
            code_title = "Code inconnu"

            for result in results[:10]:  # Limiter à 10 résultats
                # Extraire le nom du code depuis titles (premier résultat)
                if result.get("titles") and len(result["titles"]) > 0 and code_title == "Code inconnu":
                    code_title = result["titles"][0].get("title", "Code inconnu")

                # Extraire les articles depuis sections > extracts
                for section in result.get("sections", []):
                    section_title = section.get("title", "")
                    for extract in section.get("extracts", []):
                        article_num = extract.get("num", extract.get("title", ""))
                        article_id = extract.get("id", "")
                        date_version = extract.get("dateVersion", "")

                        # Extraire le texte (values contient les extraits avec <mark>)
                        text_values = extract.get("values", [])
                        text_preview = " ".join(text_values)[:300] if text_values else ""

                        article_data = {
                            "article_id": article_id,
                            "article_num": article_num,
                            "section_title": section_title,
                            "text_preview": text_preview,
                            "date_version": date_version,
                            "legal_status": extract.get("legalStatus", "")
                        }

                        # Dédupliquer par numéro d'article, garder la version la plus récente
                        if article_num:
                            if article_num not in articles_by_num:
                                articles_by_num[article_num] = article_data
                            else:
                                # Comparer les dates (garder la plus récente)
                                existing_date = articles_by_num[article_num].get("date_version", "")
                                if date_version > existing_date:
                                    articles_by_num[article_num] = article_data

            # Convertir le dict en liste d'articles uniques
            unique_articles = list(articles_by_num.values())

            print(f"[LegifranceService] Articles uniques trouvés: {len(unique_articles)}")

            # Fallback : Si pas assez d'articles et qu'on a plus de 2 concepts, relancer avec moins de concepts
            if len(unique_articles) < min_articles_wanted and len(concepts) > 2:
                print(f"[LegifranceService] ⚠️ Pas assez d'articles ({len(unique_articles)} < {min_articles_wanted})")
                print(f"[LegifranceService] 🔄 Nouvelle recherche avec les 2 premiers concepts seulement...")

                # Relancer la recherche avec seulement les 2 premiers concepts (les plus pertinents)
                fallback_search_params = {
                    "codes": codes,
                    "concepts": concepts[:2],  # Seulement les 2 premiers
                    "nature_filter": nature_filter
                }

                # Appel récursif avec concepts réduits
                return self.search(fallback_search_params, with_full_text=with_full_text, top_n=top_n)

            # Créer un seul résultat groupé avec tous les articles uniques
            formatted_results = [{
                "code_title": code_title,
                "nature": "code",
                "date": "",
                "etat": "",
                "fond": fond,
                "articles": unique_articles
            }]

            # Si demandé, récupérer le texte complet des top N articles
            if with_full_text and formatted_results:
                print(f"\n[LegifranceService] Récupération du texte complet des {top_n} meilleurs articles...")

                # Collecter les IDs des top N articles
                article_ids_to_fetch = []
                for result_idx, result in enumerate(formatted_results):
                    for article_idx, article in enumerate(result.get("articles", [])):
                        if len(article_ids_to_fetch) < top_n:
                            article_ids_to_fetch.append({
                                "id": article["article_id"],
                                "result_index": result_idx,
                                "article_index": article_idx
                            })

                # Consulter chaque article
                for item in article_ids_to_fetch:
                    article_id = item["id"]
                    full_article = self.consult(article_id)

                    # Ajouter le texte complet à l'article correspondant
                    if "error" not in full_article:
                        result_idx = item["result_index"]
                        article_idx = item["article_index"]
                        formatted_results[result_idx]["articles"][article_idx]["full_text"] = full_article.get("text", "")
                        formatted_results[result_idx]["articles"][article_idx]["full_text_html"] = full_article.get("text_html", "")
                    else:
                        print(f"[LegifranceService] ⚠️ Échec consultation {article_id}: {full_article.get('error')}")

            return {
                "results": formatted_results,
                "total": total,
                "query": search_query,
                "fond": fond
            }

        except requests.HTTPError as e:
            print(f"[LegifranceService] ❌ Erreur HTTP: {e}")
            print(f"[LegifranceService] Réponse: {e.response.text if e.response else 'N/A'}")

            # Retourner un résultat vide plutôt qu'une exception
            return {
                "results": [],
                "total": 0,
                "query": search_query,
                "error": str(e)
            }

        except Exception as e:
            print(f"[LegifranceService] ❌ Erreur: {e}")
            return {
                "results": [],
                "total": 0,
                "query": search_query,
                "error": str(e)
            }

    def consult(self, article_id: str) -> Dict:
        """
        Récupère le texte complet d'un article via l'API Legifrance /consult/getArticle

        Args:
            article_id (str): ID de l'article (ex: "LEGIARTI000006428555")

        Returns:
            Dict: Contenu complet de l'article
        """
        print(f"[LegifranceService] Consultation article: {article_id}")

        try:
            # Authentification OAuth2
            token = self._get_access_token()

            # Headers avec le token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # Endpoint pour récupérer un article
            endpoint = f"{self.api_url}/consult/getArticle"

            # Payload pour la consultation (selon la doc: {"id": "LEGIARTI..."})
            payload = {
                "id": article_id
            }

            print(f"[LegifranceService] Appel API: POST {endpoint}")
            print(f"[LegifranceService] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            # Appel API
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                print(f"[LegifranceService] ❌ Status code: {response.status_code}")
                print(f"[LegifranceService] ❌ Réponse: {response.text}")

            response.raise_for_status()

            data = response.json()

            # Debug: afficher la structure de la réponse
            print(f"[LegifranceService] Structure de la réponse:")
            print(f"[LegifranceService] Clés disponibles: {list(data.keys())}")
            if "article" in data:
                print(f"[LegifranceService] Clés dans 'article': {list(data['article'].keys())}")

            # Extraire le texte de l'article
            article_text = ""
            article_text_html = ""
            article_num = ""
            article_title = ""

            # Extraire les données depuis data['article']
            if "article" in data:
                article_obj = data["article"]
                article_text = article_obj.get("texte", "")
                article_text_html = article_obj.get("texteHtml", "")
                article_num = article_obj.get("num", "")
                # Le titre peut être dans fullSectionsTitre ou sectionParentTitre
                article_title = article_obj.get("sectionParentTitre", "")

            print(f"[LegifranceService] ✅ Article {article_num} récupéré ({len(article_text)} caractères)")

            return {
                "article_id": article_id,
                "article_num": article_num,
                "article_title": article_title,
                "text": article_text,
                "text_html": article_text_html,
                "full_data": data  # Garder toutes les données pour debug
            }

        except requests.HTTPError as e:
            print(f"[LegifranceService] ❌ Erreur HTTP: {e}")
            print(f"[LegifranceService] Réponse: {e.response.text if e.response else 'N/A'}")
            return {
                "article_id": article_id,
                "error": str(e),
                "text": ""
            }

        except Exception as e:
            print(f"[LegifranceService] ❌ Erreur: {e}")
            return {
                "article_id": article_id,
                "error": str(e),
                "text": ""
            }


# Fonction standalone pour faciliter l'import dans les pipelines
def search_legifrance(search_params: Dict) -> Dict:
    """
    Fonction utilitaire pour rechercher sur Legifrance

    Args:
        search_params (Dict): Paramètres de recherche
            {
                "codes": ["Code civil"],
                "concepts": ["PACS", "dissolution"],
                "nature_filter": ["CODE"]
            }

    Returns:
        Dict: Résultats de recherche
    """
    service = LegifranceService()
    return service.search(search_params)
