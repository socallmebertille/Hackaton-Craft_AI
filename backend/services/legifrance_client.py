"""
Module de communication avec l'API Légifrance

Ce module fournit une interface Python pour interagir avec l'API officielle
de Légifrance, permettant de rechercher et consulter des textes juridiques français.

Fonctionnalités principales:
- Authentification OAuth2 avec gestion automatique des tokens
- Recherche dans différents fonds juridiques (codes, jurisprudence, etc.)
- Consultation de textes juridiques spécifiques
- Suggestions d'autocomplétion pour faciliter les recherches
"""

import requests
from typing import Dict, List, Optional
import os


from mistralai import Mistral

class LegifranceClient:
    """
    Client pour interagir avec l'API Légifrance

    Cette classe gère l'authentification OAuth2 et fournit des méthodes
    pour rechercher et consulter des textes juridiques français.

    Attributes:
        client_id (str): Identifiant OAuth fourni par Légifrance
        client_secret (str): Secret OAuth fourni par Légifrance
        token_url (str): URL pour obtenir le token d'accès OAuth
        api_url (str): URL de base de l'API Légifrance
        access_token (str|None): Token d'accès en cache (pour éviter les appels répétés)
    """

    def __init__(self):
        """
        Initialise le client Légifrance avec les credentials OAuth

        Les credentials doivent être définis dans les variables d'environnement:
        - MIBS_LEGIFRANCE_CLIENT_ID
        - MIBS_LEGIFRANCE_CLIENT_SECRET
        - MIBS_LEGIFRANCE_TOKEN_URL
        - MIBS_LEGIFRANCE_API_URL
        - MISTRAL_API_KEY (pour l'enrichissement des requêtes)
        """
        self.client_id = os.getenv("MIBS_LEGIFRANCE_CLIENT_ID")
        self.client_secret = os.getenv("MIBS_LEGIFRANCE_CLIENT_SECRET")
        self.token_url = os.getenv("MIBS_LEGIFRANCE_TOKEN_URL")
        self.api_url = os.getenv("MIBS_LEGIFRANCE_API_URL")
        self.access_token = None

        # Client Mistral pour enrichir les requêtes de recherche
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = Mistral(api_key=mistral_api_key) if mistral_api_key else None

    def _get_access_token(self) -> str:
        """
        Obtient un token d'accès OAuth2 pour authentifier les requêtes

        Cette méthode utilise le flux "client_credentials" OAuth2.
        Le token est mis en cache pour éviter les appels répétés.

        Returns:
            str: Token d'accès valide

        Raises:
            requests.HTTPError: En cas d'échec de l'authentification
        """
        # Si on a déjà un token en cache, le réutiliser
        if self.access_token:
            return self.access_token

        # Préparer la requête OAuth2
        payload = {
            "grant_type": "client_credentials",  # Type de flux OAuth2
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid"  # Scope requis par l'API Légifrance
        }

        # Envoyer la requête d'authentification
        response = requests.post(self.token_url, data=payload)
        response.raise_for_status()  # Lever une exception si erreur HTTP

        # Extraire et mettre en cache le token d'accès
        self.access_token = response.json()["access_token"]
        return self.access_token

    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """
        Effectue une requête authentifiée à l'API Légifrance

        Cette méthode centralise la logique de requête HTTP avec:
        - Authentification automatique via token OAuth2
        - Headers appropriés pour l'API
        - Gestion des erreurs HTTP

        Args:
            endpoint (str): Endpoint de l'API (ex: "search", "consult/code")
            payload (Dict): Corps de la requête JSON

        Returns:
            Dict: Réponse JSON de l'API

        Raises:
            requests.HTTPError: En cas d'erreur HTTP (4xx, 5xx)
        """
        # Récupérer le token d'authentification
        token = self._get_access_token()

        # Préparer les headers HTTP
        headers = {
            "Authorization": f"Bearer {token}",  # Token Bearer OAuth2
            "Content-Type": "application/json"   # Format JSON
        }

        # Construire l'URL complète
        url = f"{self.api_url}/{endpoint}"

        # Envoyer la requête POST avec le payload JSON
        response = requests.post(url, json=payload, headers=headers)

        # Debug: afficher le statut et le contenu en cas d'erreur (désactivé en production)
        # if response.status_code >= 400:
        #     print(f"[Legifrance DEBUG] Erreur {response.status_code} sur {endpoint}")
        #     print(f"[Legifrance DEBUG] Payload envoyé: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        #     print(f"[Legifrance DEBUG] Réponse: {response.text[:500]}")

        response.raise_for_status()  # Lever exception si erreur HTTP

        return response.json()

    def list_docs_admins(self, years: List[int]) -> Dict:
        """
        Liste les documents administratifs pour les années données

        Args:
            years (List[int]): Liste des années à rechercher (ex: [2023, 2024])

        Returns:
            Dict: Liste des documents administratifs trouvés
        """
        payload = {
            "years": years
        }
        return self._make_request("list/docsAdmins", payload)

    def search(self,
               query: str,
               fond: str = "LODA_DATE",
               nature_values: list = None,
               page_number: int = 1,
               page_size: int = 10) -> Dict:
        """
        Recherche dans les textes juridiques selon différents critères

        Cette méthode permet de rechercher dans différents fonds juridiques
        (codes, jurisprudence, lois, etc.) avec pagination.

        Args:
            query (str): Texte de recherche (ex: "contrat de travail")
            fond (str): Type de fond juridique à rechercher:
                - LODA_DATE: Lois, ordonnances, décrets et arrêtés
                - CODE_DATE: Codes en vigueur
                - JURI_DATE: Jurisprudence (judiciaire et administrative)
                - CONSTIT_DATE: Textes constitutionnels
            nature_values (list): Liste des natures de documents à filtrer (ex: ["LOI", "ORDONNANCE"])
                Si None, pas de filtre de nature
            page_number (int): Numéro de la page (commence à 1)
            page_size (int): Nombre de résultats par page

        Returns:
            Dict: Résultats de recherche avec pagination
                {
                    "results": [...],  # Liste des textes trouvés
                    "totalResultNumber": int,  # Nombre total de résultats
                    "pageNumber": int,
                    "pageSize": int
                }
        """
        # Construire le payload selon le format CORRECT de l'API Légifrance
        payload = {
            "fond": fond,  # Le fond est au niveau racine
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "ALL",  # Recherche dans tous les champs
                        "criteres": [
                            {
                                "typeRecherche": "UN_DES_MOTS",
                                "valeur": query,
                                "operateur": "ET"
                            }
                        ],
                        "operateur": "ET"
                    }
                ],
                "sort": "PERTINENCE",
                "secondSort": "ID",
                "operateur": "ET",
                "typePagination": "DEFAUT",
                "pageNumber": page_number,
                "pageSize": page_size,
                "fromAdvancedRecherche": False
            }
        }

        # Ajouter les filtres de nature si spécifiés
        if nature_values:
            payload["recherche"]["filtres"] = [
                {
                    "facette": "NATURE",
                    "valeurs": nature_values  # IMPORTANT: "valeurs" (pluriel) avec array
                }
            ]

        return self._make_request("search", payload)

    def consult_code(self, textId: str, date: Optional[str] = None) -> Dict:
        """
        Consulte le contenu complet d'un texte juridique (code, loi, etc.)

        Cette méthode permet de récupérer le texte intégral d'un document
        juridique identifié par son ID. Elle permet également de consulter
        une version historique du texte à une date donnée.

        Args:
            textId (str): Identifiant unique du texte (obtenu via search())
            date (Optional[str]): Date de consultation au format YYYY-MM-DD
                                 Si None, retourne la version actuellement en vigueur

        Returns:
            Dict: Contenu complet du texte juridique incluant:
                - Titre et métadonnées
                - Articles et leur contenu
                - Structure hiérarchique (chapitres, sections, etc.)
        """
        payload = {
            "textId": textId, # "textId": "LEGITEXT000006075116"
            "abrogated": False,
            "searchedString": "", #"constitution 1958",
            "date": "", #"2021-04-15",
            "fromSuggest": True,
            "sctCid": "" #"LEGISCTA000006112861"
        }
        # Ajouter la date si spécifiée (pour consulter une version historique)
        if date:
            payload["date"] = date

        return self._make_request("consult/code", payload)

    def consult_juri(self, textId: str) -> Dict:
        """
        Consulte une décision de jurisprudence

        Récupère le contenu complet d'une décision de justice (arrêt, jugement, etc.)

        Args:
            textId (str): Identifiant unique de la décision

        Returns:
            Dict: Contenu de la décision incluant:
                - Juridiction et date
                - Numéro de pourvoi/RG
                - Texte intégral de la décision
                - Résumé et mots-clés
        """
        payload = {
            "textId": textId
        }
        return self._make_request("consult/juri", payload)

    def suggest(self, query: str, type_suggestion: str = "CODE") -> Dict:
        """
        Obtient des suggestions d'autocomplétion pour faciliter la recherche

        Cette méthode propose des suggestions basées sur le début de la requête,
        similaire à l'autocomplétion d'un moteur de recherche.

        Args:
            query (str): Texte partiel pour lequel obtenir des suggestions
            type_suggestion (str): Type de suggestions à obtenir:
                - "CODE": Suggestions de codes (Code civil, Code pénal, etc.)
                - "ARTICLE": Suggestions d'articles spécifiques
                - "JURI": Suggestions de jurisprudence

        Returns:
            Dict: Liste de suggestions pertinentes
        """
        # Selon la doc officielle, l'endpoint /suggest utilise cette structure:
        # - searchText: le texte de recherche
        # - supplies: liste des fonds à interroger (JORF, JURI, etc.)
        # - documentsDits: boolean pour activer les suggestions de documents dits (ex: "Loi Macron")
        payload = {
            "searchText": query,
            "supplies": ["JORF", "JURI", "LODA"],  # Fonds supportés par suggest
            "documentsDits": True
        }

        return self._make_request("suggest", payload)

    def _extract_legal_concepts(self, question: str) -> str:
        """
        Utilise Mistral pour extraire les concepts juridiques d'une question en langage naturel

        Transforme automatiquement "Mon mari m'a trompé" en termes comme
        "PACS dissolution obligations partenaires infidélité"

        Args:
            question (str): Question en langage naturel

        Returns:
            str: Termes juridiques extraits pour améliorer la recherche Legifrance
        """
        # Si Mistral n'est pas disponible, retourner la question originale
        if not self.mistral_client:
            return question

        try:
            # Prompt pour extraire les concepts juridiques
            response = self.mistral_client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extrait UNIQUEMENT les concepts juridiques de cette question en quelques mots-clés français.

Question: {question}

Réponds avec SEULEMENT les termes juridiques pertinents séparés par des espaces (max 15 mots).
IMPORTANT: Ajoute TOUJOURS le nom du code juridique concerné (Code civil, Code du travail, etc.)

Exemples:
- "Mon mari m'a trompé, on est pacsé" -> "Code civil PACS article 515 dissolution obligations partenaires infidélité devoir fidélité"
- "Peut-on rompre un CDD avant la fin?" -> "Code du travail CDD rupture anticipée contrat durée déterminée"
- "Mon employeur ne me paie pas" -> "Code du travail salaire rémunération employeur paiement"

Termes juridiques:"""
                    }
                ],
                temperature=0.3,  # Faible température pour des résultats cohérents
                max_tokens=50
            )

            legal_terms = response.choices[0].message.content.strip()
            return legal_terms if legal_terms else question

        except Exception as e:
            print(f"[Legifrance] Erreur extraction concepts: {e}")
            return question

    def search_comprehensive(self, question: str) -> Dict:
        """
        Effectue une recherche juridique complète et multi-sources

        Cette méthode orchestre une recherche approfondie en combinant
        plusieurs appels API pour obtenir un maximum d'informations pertinentes:
        1. Recherche dans plusieurs fonds juridiques (codes, jurisprudence, constitution)
        2. Consultation du contenu complet des textes les plus pertinents
        3. Suggestions de termes et documents connexes

        Args:
            question (str): Question juridique à rechercher
                          (ex: "conditions de validité d'un contrat de travail")

        Returns:
            Dict: Dictionnaire structuré contenant:
                {
                    "question": str,              # Question d'origine
                    "search_results": List[Dict], # Tous les résultats trouvés
                    "consulted_texts": List[Dict],# Contenu complet des 3 meilleurs résultats
                    "suggestions": Dict           # Suggestions de recherches connexes
                }

        Note:
            Les erreurs sur des fonds individuels sont gérées silencieusement
            pour permettre de retourner les résultats des autres fonds.
        """
        # Initialiser la structure de résultats
        results = {
            "question": question,
            "search_results": [],
            "consulted_texts": [],
            "suggestions": []
        }

        # Enrichir la question avec des concepts juridiques
        legal_query = self._extract_legal_concepts(question)
        print(f"[Legifrance] Question originale: {question}")
        print(f"[Legifrance] Termes juridiques extraits: {legal_query}")

        # 1. RECHERCHE: Interroger plusieurs fonds juridiques en parallèle
        # On recherche dans les sources principales du droit français
        # IMPORTANT: CODE_DATE en premier pour privilégier le Code civil, pénal, etc.
        fonds_to_search = [
            ("CODE_DATE", None),                              # Codes (Code civil, Code pénal, etc.) - PRIORITAIRE
            ("LODA_DATE", ["LOI", "ORDONNANCE"]),            # Lois et ordonnances (sans décrets pour éviter bruit)
            ("JURI", None),                                   # Jurisprudence judiciaire (Cour de cassation)
            ("CETAT", None)                                   # Jurisprudence administrative (Conseil d'État)
        ]

        for fond, nature_values in fonds_to_search:
            try:
                # Rechercher dans ce fond avec les termes juridiques enrichis (5 résultats max par fond)
                search_result = self.search(legal_query, fond=fond, nature_values=nature_values, page_size=5)

                # Agréger les résultats de tous les fonds
                if "results" in search_result:
                    results["search_results"].extend(search_result["results"])
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres fonds
                print(f"Erreur lors de la recherche dans {fond}: {e}")

        # 2. CONSULTATION: Récupérer le contenu complet des 3 textes les plus pertinents
        # L'API de recherche ne retourne pas le texte complet, il faut consulter avec l'ID
        for result in results["search_results"][:3]:  # Top 3 résultats
            try:
                # L'ID du texte est dans titles[0].id
                titles = result.get("titles", [])
                if titles and titles[0].get("id"):
                    text_id = titles[0]["id"]

                    # Choisir le bon endpoint de consultation selon le type de texte
                    nature = result.get("nature", "")
                    origin = result.get("origin", "")

                    try:
                        # Déterminer l'endpoint approprié selon la nature du texte
                        # IMPORTANT: Vérifier la nature AVANT l'origin car les codes ont origin="LEGI"
                        if nature and nature.lower() == "code":
                            # Codes (Code civil, Code pénal, etc.) -> consult/code
                            # Nettoyer le textId pour enlever la date (format: LEGITEXT000006070721_24-12-1958)
                            clean_text_id = text_id.split("_")[0] if "_" in text_id else text_id

                            # Construire le payload complet pour consult/code
                            # Essayer avec seulement les paramètres obligatoires
                            payload = {
                                "textId": clean_text_id,
                                "date": "2024-01-01"
                            }

                            consulted = self._make_request("consult/code", payload)

                            # Formater le contenu des articles des codes
                            if consulted.get("articles"):
                                articles_text = []
                                for article in consulted["articles"][:10]:  # Limiter à 10 articles
                                    num = article.get("num", "")
                                    content = article.get("content", "")
                                    if content:
                                        articles_text.append(f"Article {num}: {content}")
                                consulted["text"] = "\n\n".join(articles_text)
                            else:
                                consulted["text"] = consulted.get("visa", "")

                        elif nature in ["DECRET", "LOI", "ORDONNANCE"] or origin == "LEGI":
                            # Lois, ordonnances, décrets -> consult/legiPart
                            payload = {
                                "textId": text_id,
                                "date": result.get("date", "").split("T")[0] if result.get("date") else None,
                                "searchedString": question  # Pour contexte
                            }
                            consulted = self._make_request("consult/legiPart", payload)

                            # Formater le contenu des articles en texte lisible
                            if consulted.get("articles"):
                                articles_text = []
                                for article in consulted["articles"][:10]:  # Limiter à 10 articles
                                    num = article.get("num", "")
                                    content = article.get("content", "")
                                    if content:
                                        articles_text.append(f"Article {num}: {content}")
                                consulted["text"] = "\n\n".join(articles_text)
                            else:
                                consulted["text"] = consulted.get("visa", "")  # Fallback sur les visas

                        elif origin == "JURI" or origin == "CETAT":
                            # Jurisprudence -> consult/juri
                            consulted = self.consult_juri(text_id)
                        else:
                            # Cas non géré - utiliser les métadonnées
                            print(f"[Legifrance] Type de texte non géré: nature={nature}, origin={origin}")
                            consulted = {
                                "title": titles[0].get("title", ""),
                                "nature": nature,
                                "text": f"Type de texte non géré: {nature}/{origin}",
                                "origin": origin
                            }

                        results["consulted_texts"].append(consulted)
                    except Exception as e:
                        # Si la consultation échoue, utiliser au moins les métadonnées du résultat
                        print(f"[Legifrance] Impossible de consulter {text_id} ({nature}): {e}")

                        # Extraire le maximum d'informations disponibles du résultat de recherche
                        title = titles[0].get("title", "") if titles else ""
                        summary = result.get("summary", "")
                        num = result.get("num", "")

                        # Construire un texte informatif avec les métadonnées
                        metadata_text = f"Référence: {title}"
                        if num:
                            metadata_text += f"\nNuméro: {num}"
                        if summary:
                            metadata_text += f"\nRésumé: {summary}"
                        metadata_text += f"\n\nNote: Le texte complet n'est pas disponible via l'API sandbox pour les {nature}. Utilisez vos connaissances juridiques sur ce texte pour argumenter."

                        results["consulted_texts"].append({
                            "title": title,
                            "nature": nature,
                            "text": metadata_text,
                            "num": num,
                            "date": result.get("date", ""),
                            "origin": origin,
                            "summary": summary
                        })
            except Exception as e:
                print(f"[Legifrance] Erreur extraction texte: {e}")

        # 3. SUGGESTIONS: Désactivé car problèmes avec le sandbox API
        # Les suggestions ne sont pas critiques pour le débat
        # try:
        #     suggestions = self.suggest(question)
        #     results["suggestions"] = suggestions
        # except Exception as e:
        #     print(f"Erreur lors de l'obtention des suggestions: {e}")

        return results
