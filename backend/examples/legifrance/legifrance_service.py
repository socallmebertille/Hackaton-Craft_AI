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

    def search(self, search_params: Dict, with_full_text: bool = False, top_n: int = 5, original_question: str = None, include_jurisprudence: bool = False) -> Dict:
        """
        Recherche des textes juridiques sur Legifrance

        Args:
            search_params (Dict): Paramètres de recherche issus de Mistral
                {
                    "codes": ["Code civil"],
                    "concepts": ["PACS", "dissolution", "rupture"],
                    "nature_filter": ["CODE"],
                    "question": "Quelles sont les lois sur la dissolution du PACS ?" (optionnel)
                }
            with_full_text (bool): Si True, récupère le texte complet des top_n meilleurs articles
            top_n (int): Nombre d'articles dont on veut le texte complet (défaut: 5)
            original_question (str): Question originale pour le filtrage intelligent (optionnel)
            include_jurisprudence (bool): Si True, recherche aussi dans les jurisprudences en plus des codes (défaut: False)

        Returns:
            Dict: {
                "results": [
                    {
                        "code_title": "Code civil",
                        "nature": "code",  # ou "jurisprudence"
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
        question = search_params.get("question") or original_question  # Récupérer la question

        # Stratégie de recherche optimisée ADAPTATIVE :
        # - 1 concept: Recherche simple UN_DES_MOTS
        # - 2-3 concepts: Tous sont OBLIGATOIRES (ex: "PACS" ET "dissolution" ET "rupture")
        # - 4+ concepts: Les 2 premiers sont obligatoires, le reste optionnel
        #    → Exemple: "décès" ET "héritier" ET ("succession" OU "ordre")
        #    → Équilibre entre précision (pas d'articles hors-sujet) et recall (trouver les bons articles)

        print(f"[LegifranceService] Concepts: {concepts}")
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

        # Construire les critères de recherche
        criteres = []
        search_query = " ".join(concepts) if concepts else ""  # Pour la compatibilité avec le reste du code

        if concepts:
            if len(concepts) == 1:
                # Si un seul concept, recherche simple
                criteres = [{
                    "typeRecherche": "UN_DES_MOTS",
                    "valeur": concepts[0],
                    "operateur": "ET"
                }]
                print(f"[LegifranceService] Critère unique: '{concepts[0]}'")
            elif len(concepts) <= 3:
                # Avec 2-3 concepts: chaque concept devient un critère obligatoire séparé
                # Ex: "PACS" ET "dissolution"
                # Ex: "licenciement" ET "arrêt maladie" ET "inaptitude"
                for concept in concepts:
                    criteres.append({
                        "typeRecherche": "UN_DES_MOTS",
                        "valeur": concept,
                        "operateur": "ET"
                    })
                concept_list = "' ET '".join(concepts)
                print(f"[LegifranceService] Stratégie: '{concept_list}' (tous les critères obligatoires)")
            else:
                # Avec 4+ concepts: les 2 premiers sont obligatoires, les autres optionnels
                # Ex: "héritier" ET "succession" ET ("décès" OU "ordre")
                # Critères obligatoires (2 premiers)
                for concept in concepts[:2]:
                    criteres.append({
                        "typeRecherche": "UN_DES_MOTS",
                        "valeur": concept,
                        "operateur": "ET"
                    })

                # Critères optionnels (reste)
                optional_concepts = " ".join(concepts[2:])
                criteres.append({
                    "typeRecherche": "UN_DES_MOTS",
                    "valeur": optional_concepts,
                    "operateur": "ET"
                })

                print(f"[LegifranceService] Stratégie: '{concepts[0]}' ET '{concepts[1]}' ET (au moins un de: {concepts[2:]})")
        else:
            # Fallback si pas de concepts
            criteres = [{
                "typeRecherche": "UN_DES_MOTS",
                "valeur": "",
                "operateur": "ET"
            }]

        payload = {
            "fond": fond,
            "recherche": {
                "champs": [{
                    "typeChamp": "ARTICLE",  # Recherche dans les articles
                    "criteres": criteres,
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

            print(f"[LegifranceService] Articles bruts trouvés (avant filtrage): {len(unique_articles)}")

            # ÉTAPE DE FILTRAGE INTELLIGENT avec Mistral
            # Si on a une question et des articles, filtrer pour ne garder que les pertinents
            # Toujours filtrer dès qu'on a au moins 1 article
            if question and unique_articles and len(unique_articles) >= 1:
                print(f"\n[LegifranceService] 🧠 Filtrage intelligent avec Mistral...")
                from services.mistral_service import MistralService

                mistral = MistralService()
                filtered_articles = mistral.filter_relevant_articles(
                    question=question,
                    articles=unique_articles,
                    concepts=concepts
                )

                if filtered_articles:
                    unique_articles = filtered_articles
                    print(f"[LegifranceService] ✅ Articles après filtrage: {len(unique_articles)}")
                else:
                    print(f"[LegifranceService] ⚠️ Aucun article pertinent trouvé, conservation de tous les articles")

            # Créer un seul résultat groupé avec tous les articles (filtrés si applicable)
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

            # Si demandé, rechercher aussi dans les jurisprudences
            if include_jurisprudence:
                print(f"\n[LegifranceService] 📚 Recherche complémentaire dans les JURISPRUDENCES...")

                try:
                    jurisprudence_results = self._search_jurisprudence(
                        search_query=search_query,
                        concepts=concepts,
                        question=question,
                        max_results=10  # Analyser 10 jurisprudences pour mieux filtrer
                    )

                    if jurisprudence_results:
                        print(f"[LegifranceService] ✅ {len(jurisprudence_results)} jurisprudences ajoutées")
                        formatted_results.extend(jurisprudence_results)
                    else:
                        print(f"[LegifranceService] Aucune jurisprudence pertinente trouvée")

                except Exception as e:
                    print(f"[LegifranceService] ⚠️ Erreur recherche jurisprudence: {e}")
                    # Continuer même si la recherche de jurisprudence échoue

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

    def _search_jurisprudence(self, search_query: str, concepts: list, question: str = None, max_results: int = 3) -> list:
        """
        Recherche dans les jurisprudences (décisions de justice)

        Args:
            search_query (str): Requête de recherche
            concepts (list): Liste des concepts juridiques
            question (str): Question originale pour filtrage
            max_results (int): Nombre max de jurisprudences à retourner

        Returns:
            list: Liste de résultats de jurisprudence au format standardisé
        """
        print(f"[LegifranceService] Recherche jurisprudence: '{search_query}'")

        try:
            # Obtenir le token
            token = self._get_access_token()

            # Headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            url = f"{self.api_url}/search"

            # Payload pour recherche dans les jurisprudences
            # Format selon documentation officielle Légifrance
            payload = {
                "fond": "JURI",  # Fond jurisprudence judiciaire
                "recherche": {
                    "champs": [{
                        "criteres": [{
                            "valeur": search_query,
                            "proximite": 2,
                            "operateur": "ET",
                            "typeRecherche": "UN_DES_MOTS"
                        }],
                        "operateur": "ET",
                        "typeChamp": "ALL"
                    }],
                    "fromAdvancedRecherche": False,
                    "pageSize": 20,  # Limiter le nombre de résultats
                    "operateur": "ET",
                    "typePagination": "DEFAUT",
                    "pageNumber": 1,
                    "sort": "PERTINENCE",
                    "secondSort": "DATE_DESC"
                }
            }

            print(f"[LegifranceService] Appel API JURI (jurisprudence judiciaire)")

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])
            total = data.get("totalResultNumber", 0)

            print(f"[LegifranceService] {total} jurisprudences trouvées")

            # Parser les jurisprudences
            jurisprudences = []

            for result in results[:max_results]:
                # Extraire les informations de la décision
                decision_id = result.get("id", "")
                titles = result.get("titles", [])
                decision_title = titles[0].get("title", "Décision") if titles else "Décision"

                # Extraire les extraits pertinents
                sections = result.get("sections", [])
                extracts_text = []

                for section in sections[:2]:  # Limiter aux 2 premières sections
                    for extract in section.get("extracts", [])[:2]:  # 2 extraits par section
                        values = extract.get("values", [])
                        if values:
                            extracts_text.append(" ".join(values)[:200])

                text_preview = " [...] ".join(extracts_text) if extracts_text else ""

                # Ajouter la jurisprudence
                jurisprudences.append({
                    "article_id": decision_id,
                    "article_num": decision_title,
                    "text_preview": text_preview,
                    "section_title": "Jurisprudence",
                    "date_version": result.get("dateDecision", ""),
                    "legal_status": "VIGUEUR"
                })

            # Filtrage intelligent avec Mistral si on a une question
            if question and jurisprudences:
                print(f"[LegifranceService] 🧠 Filtrage intelligent des jurisprudences...")
                from services.mistral_service import MistralService

                mistral = MistralService()
                filtered_juris = mistral.filter_relevant_articles(
                    question=question,
                    articles=jurisprudences,
                    concepts=concepts
                )

                if filtered_juris:
                    jurisprudences = filtered_juris
                    print(f"[LegifranceService] ✅ Jurisprudences après filtrage: {len(jurisprudences)}")

            # Retourner au format standardisé
            if jurisprudences:
                return [{
                    "code_title": "Jurisprudence",
                    "nature": "jurisprudence",
                    "date": "",
                    "etat": "",
                    "fond": "JURI",
                    "articles": jurisprudences
                }]

            return []

        except Exception as e:
            print(f"[LegifranceService] ⚠️ Erreur recherche jurisprudence: {e}")
            return []

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
