"""
Formatage et nettoyage des données juridiques

Gère le formatage des résultats des pipelines pour l'affichage
et le nettoyage des données avant envoi aux pipelines.
"""

from typing import Dict, Any, List


class DataFormatter:
    """Classe pour formater et nettoyer les données juridiques"""

    @staticmethod
    def clean_legal_data(legal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie les données juridiques en supprimant les champs vides ou None

        Args:
            legal_data: Données brutes de P1

        Returns:
            dict: Données nettoyées
        """
        cleaned = {
            "codes": [],
            "jurisprudence": [],
            "total_codes": legal_data.get("total_codes", 0),
            "total_jurisprudence": legal_data.get("total_jurisprudence", 0)
        }

        # Nettoyer les codes
        for code in legal_data.get("codes", []):
            cleaned_code = {
                "type": code.get("type", "CODE"),
                "code_title": code.get("code_title", ""),
                "article_num": code.get("article_num", ""),
                "article_id": code.get("article_id", ""),
                "text_preview": code.get("text_preview", ""),
                "legal_status": code.get("legal_status", "")
            }
            # Supprimer les champs vides pour réduire la taille
            cleaned_code = {k: v for k, v in cleaned_code.items() if v}
            cleaned["codes"].append(cleaned_code)

        # Nettoyer la jurisprudence - IMPORTANT: supprimer les champs None/vides
        for juris in legal_data.get("jurisprudence", []):
            cleaned_juris = {
                "type": juris.get("type", "JURISPRUDENCE"),
                "title": juris.get("title", ""),
                "text_preview": juris.get("text_preview", "")
            }
            # Ajouter decision_id et date seulement s'ils existent et ne sont pas vides
            if juris.get("decision_id"):
                cleaned_juris["decision_id"] = juris["decision_id"]
            if juris.get("date"):
                cleaned_juris["date"] = juris["date"]
            if juris.get("juridiction"):
                cleaned_juris["juridiction"] = juris["juridiction"]

            # Supprimer les champs vides
            cleaned_juris = {k: v for k, v in cleaned_juris.items() if v}
            cleaned["jurisprudence"].append(cleaned_juris)

        return cleaned

    @staticmethod
    def _ensure_string(value) -> str:
        """
        Convertit n'importe quelle valeur en string

        Args:
            value: Valeur à convertir

        Returns:
            str: Valeur convertie en string
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, list):
            return " ".join([DataFormatter._ensure_string(v) for v in value])
        else:
            return str(value)

    @staticmethod
    def structure_debate_messages(debate_result: Dict[str, Any]) -> List[str]:
        """
        Structure le débat en plusieurs messages séparés

        Args:
            debate_result: Résultat du Pipeline 3

        Returns:
            list: Liste de messages structurés
        """
        messages = []

        # Message 1: Positions du débat
        position_pour = debate_result.get("position_pour", "")
        position_contre = debate_result.get("position_contre", "")
        if position_pour or position_contre:
            positions_text = "## Positions du débat\n"
            if position_pour:
                positions_text += f"**POUR** : {DataFormatter._ensure_string(position_pour)}\n\n"
            if position_contre:
                positions_text += f"**CONTRE** : {DataFormatter._ensure_string(position_contre)}"
            messages.append(positions_text)

        # Message 2: Arguments POUR Round 1
        pour_r1 = debate_result.get("pour_round_1", "")
        if pour_r1:
            messages.append(f"## Arguments POUR\n{DataFormatter._ensure_string(pour_r1)}")

        # Message 3: Arguments CONTRE Round 1
        contre_r1 = debate_result.get("contre_round_1", "")
        if contre_r1:
            messages.append(f"## Arguments CONTRE\n{DataFormatter._ensure_string(contre_r1)}")

        # Message 4: Réfutation POUR Round 2
        pour_r2 = debate_result.get("pour_round_2", "")
        if pour_r2:
            messages.append(f"## Réfutation et renforcement POUR\n{DataFormatter._ensure_string(pour_r2)}")

        # Message 5: Réfutation CONTRE Round 2
        contre_r2 = debate_result.get("contre_round_2", "")
        if contre_r2:
            messages.append(f"## Réfutation et renforcement CONTRE\n{DataFormatter._ensure_string(contre_r2)}")

        # Message 6: Synthèse
        synthese = debate_result.get("synthese", "")
        if synthese:
            messages.append(f"## Synthèse\n{DataFormatter._ensure_string(synthese)}")

        # Message 7: Sources citées
        sources = debate_result.get("sources_citees", [])
        if sources:
            sources_str = []
            for s in sources:
                if isinstance(s, str):
                    sources_str.append(s)
                elif isinstance(s, list):
                    sources_str.extend([str(x) for x in s])
                else:
                    sources_str.append(str(s))

            sources_text = "## Sources juridiques citées\n"
            # Une source par ligne avec bullet point
            for source in sources_str:
                sources_text += f"• {source}\n"
            messages.append(sources_text)

        return messages

    @staticmethod
    def format_citation_result(citation_result: Dict[str, Any]) -> str:
        """
        Formate le résultat des citations pour l'utilisateur

        Args:
            citation_result: Résultat du Pipeline 4

        Returns:
            str: Citations formatées avec explications concises
        """
        response_parts = []

        # Articles de code avec explications
        codes_expliques = citation_result.get("codes_expliques", [])
        if codes_expliques:
            response_parts.append("# Articles de Code\n")
            for code in codes_expliques:
                reference = code.get("reference", "")
                explanation = code.get("explanation", "")
                if reference and explanation:
                    response_parts.append(f"• **{reference}** : {explanation}\n")

        # Jurisprudence avec explications
        juris_expliquee = citation_result.get("jurisprudence_expliquee", [])
        if juris_expliquee:
            response_parts.append("\n# Jurisprudence\n")
            for juris in juris_expliquee:
                reference = juris.get("reference", "")
                explanation = juris.get("explanation", "")
                if reference and explanation:
                    response_parts.append(f"• **{reference}** : {explanation}\n")

        # Résumé
        total_codes = citation_result.get("total_codes", 0)
        total_juris = citation_result.get("total_jurisprudence", 0)
        if total_codes > 0 or total_juris > 0:
            response_parts.append(f"\n**Total** : {total_codes} article(s) de code, {total_juris} jurisprudence(s)")

        return "\n".join(response_parts)
