"""
Schémas Pydantic pour la feature Debate
"""
from typing import Optional, Dict
from pydantic import BaseModel, Field, validator
import re
import html

# ========== CONSTANTES DE SÉCURITÉ ==========

# Limites de taille pour prévenir les abus
MAX_QUESTION_LENGTH = 1000  # Caractères max pour une question
MIN_QUESTION_LENGTH = 10    # Caractères min pour une question

# Patterns de détection d'injections de prompt
DANGEROUS_PATTERNS = [
    r'ignore\s+(previous|above|all)\s+(instructions?|prompts?|commands?)',
    r'system\s*:\s*you\s+are',
    r'<\s*script\s*>',
    r'javascript\s*:',
    r'on(load|error|click)\s*=',
    r'eval\s*\(',
    r'exec\s*\(',
]

# Compiler les regex pour performance
DANGEROUS_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


# ========== FONCTIONS DE SÉCURITÉ ==========

def sanitize_input(text: str) -> str:
    """
    Nettoie et sécurise le texte d'entrée utilisateur

    Protections:
    - Échappe les caractères HTML spéciaux (prévention XSS)
    - Supprime les caractères de contrôle dangereux
    - Normalise les espaces

    Args:
        text (str): Texte brut de l'utilisateur

    Returns:
        str: Texte nettoyé et sécurisé
    """
    # Échapper les caractères HTML pour prévenir XSS
    text = html.escape(text)

    # Supprimer les caractères de contrôle (sauf newline, tab, carriage return)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    # Normaliser les espaces multiples
    text = re.sub(r'\s+', ' ', text)

    # Trim
    text = text.strip()

    return text


def detect_prompt_injection(text: str) -> bool:
    """
    Détecte les tentatives d'injection de prompt

    Vérifie si le texte contient des patterns suspects qui pourraient
    tenter de manipuler le LLM (ex: "ignore previous instructions").

    Args:
        text (str): Texte à analyser

    Returns:
        bool: True si une injection est détectée, False sinon
    """
    text_lower = text.lower()

    # Vérifier chaque pattern dangereux
    for pattern in DANGEROUS_REGEX:
        if pattern.search(text_lower):
            return True

    return False


# ========== MODÈLES PYDANTIC ==========

class QuestionRequest(BaseModel):
    """
    Modèle de requête pour soumettre une question juridique

    Validations de sécurité:
    - Longueur entre MIN_QUESTION_LENGTH et MAX_QUESTION_LENGTH
    - Pas de caractères spéciaux dangereux
    - Détection d'injection de prompt

    Attributes:
        question (str): Question juridique posée par l'utilisateur
    """
    question: str = Field(
        ...,
        min_length=MIN_QUESTION_LENGTH,
        max_length=MAX_QUESTION_LENGTH,
        description="Question juridique (10-1000 caractères)"
    )

    @validator('question')
    def validate_question(cls, v):
        """
        Validation personnalisée de la question

        Vérifie:
        1. Pas uniquement des espaces
        2. Pas de tentatives d'injection de prompt
        3. Sanitization du contenu

        Args:
            v (str): Valeur de la question

        Returns:
            str: Question validée et nettoyée

        Raises:
            ValueError: Si la validation échoue
        """
        # Nettoyer le texte
        cleaned = sanitize_input(v)

        # Vérifier qu'il reste du contenu après nettoyage
        if not cleaned or len(cleaned.strip()) < MIN_QUESTION_LENGTH:
            raise ValueError(
                f"La question doit contenir au moins {MIN_QUESTION_LENGTH} caractères significatifs"
            )

        # Détecter les tentatives d'injection de prompt
        if detect_prompt_injection(cleaned):
            raise ValueError(
                "Votre question contient des patterns suspects. "
                "Veuillez reformuler votre question juridique de manière claire et directe."
            )

        return cleaned


class DebateResponse(BaseModel):
    """
    Modèle de réponse immédiate après soumission d'une question

    Retourné par POST /api/debate/submit pour confirmer que le débat
    a été accepté et lancé en arrière-plan.

    Attributes:
        debate_id (str): UUID unique identifiant ce débat
        status (str): Statut initial (toujours "processing")
        message (str): Message explicatif pour l'utilisateur
    """
    debate_id: str
    status: str
    message: str


class DebateResult(BaseModel):
    """
    Modèle de résultat complet d'un débat

    Retourné par GET /api/debate/{id} pour donner l'état détaillé
    d'un débat (en cours ou terminé).

    Attributes:
        debate_id (str): UUID du débat
        status (str): Statut actuel ("processing", "completed", "error")
        question (str): Question juridique d'origine
        legal_context (Optional[Dict]): Contexte Légifrance (None si en cours)
        debate_rounds (Optional[list]): Liste des arguments (None si en cours)
        summary (Optional[str]): Résumé final (None si en cours/erreur)
        created_at (str): Timestamp de création (ISO format)
        completed_at (Optional[str]): Timestamp de fin (None si en cours)
    """
    debate_id: str
    status: str
    question: str
    legal_context: Optional[Dict] = None
    debate_rounds: Optional[list] = None
    summary: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
