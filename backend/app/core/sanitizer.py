"""
Module de sanitization pour la protection contre les injections XSS
"""

import bleach
from typing import Optional


# Configuration des tags et attributs HTML autorisés (très restrictif pour un chat juridique)
ALLOWED_TAGS = [
    # Formatage de texte basique
    'p', 'br', 'strong', 'em', 'u', 'code', 'pre',
    # Listes
    'ul', 'ol', 'li',
    # Titres
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Citations
    'blockquote',
]

ALLOWED_ATTRIBUTES = {
    # Aucun attribut autorisé pour maximiser la sécurité
    '*': []
}

# Longueurs maximales pour prévenir les attaques DoS
MAX_MESSAGE_LENGTH = 10000  # 10k caractères pour un message
MAX_TITLE_LENGTH = 200      # 200 caractères pour un titre
MAX_EMAIL_LENGTH = 254      # Longueur max standard d'un email
MAX_NAME_LENGTH = 100       # 100 caractères pour nom/prénom/entreprise


def sanitize_html(text: str, strip: bool = True) -> str:
    """
    Nettoie le texte HTML pour prévenir les attaques XSS

    Args:
        text: Texte à nettoyer
        strip: Si True, supprime tous les tags HTML. Si False, garde les tags autorisés.

    Returns:
        str: Texte nettoyé
    """
    if not text:
        return ""

    if strip:
        # Mode strict : supprime tous les tags HTML
        return bleach.clean(text, tags=[], attributes={}, strip=True)
    else:
        # Mode permissif : garde les tags autorisés (pour ReactMarkdown)
        return bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )


def sanitize_message(message: str) -> str:
    """
    Nettoie un message utilisateur

    Args:
        message: Message à nettoyer

    Returns:
        str: Message nettoyé

    Raises:
        ValueError: Si le message dépasse la longueur maximale
    """
    if not message:
        return ""

    # Vérifier la longueur
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Le message ne peut pas dépasser {MAX_MESSAGE_LENGTH} caractères")

    # Nettoyer (supprimer tous les tags HTML)
    cleaned = sanitize_html(message.strip(), strip=True)

    return cleaned


def sanitize_text_field(text: str, max_length: Optional[int] = None, field_name: str = "Champ") -> str:
    """
    Nettoie un champ texte générique (nom, prénom, entreprise, etc.)

    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale autorisée
        field_name: Nom du champ (pour les messages d'erreur)

    Returns:
        str: Texte nettoyé

    Raises:
        ValueError: Si le texte dépasse la longueur maximale
    """
    if not text:
        return ""

    # Vérifier la longueur
    if max_length and len(text) > max_length:
        raise ValueError(f"{field_name} ne peut pas dépasser {max_length} caractères")

    # Nettoyer (supprimer tous les tags HTML)
    cleaned = sanitize_html(text.strip(), strip=True)

    return cleaned


def sanitize_email(email: str) -> str:
    """
    Nettoie une adresse email

    Args:
        email: Email à nettoyer

    Returns:
        str: Email nettoyé (en minuscules)

    Raises:
        ValueError: Si l'email est invalide ou trop long
    """
    if not email:
        return ""

    # Vérifier la longueur
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(f"L'email ne peut pas dépasser {MAX_EMAIL_LENGTH} caractères")

    # Nettoyer et normaliser
    cleaned = sanitize_html(email.strip(), strip=True).lower()

    return cleaned


def validate_and_sanitize_user_input(
    message: Optional[str] = None,
    title: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
    prenom: Optional[str] = None,
    entreprise: Optional[str] = None
) -> dict:
    """
    Fonction tout-en-un pour valider et nettoyer les inputs utilisateurs

    Args:
        message: Message de chat
        title: Titre
        email: Email
        name: Nom
        prenom: Prénom
        entreprise: Entreprise

    Returns:
        dict: Dictionnaire avec les champs nettoyés

    Raises:
        ValueError: Si un champ est invalide
    """
    result = {}

    if message is not None:
        result['message'] = sanitize_message(message)

    if title is not None:
        result['title'] = sanitize_text_field(title, MAX_TITLE_LENGTH, "Titre")

    if email is not None:
        result['email'] = sanitize_email(email)

    if name is not None:
        result['name'] = sanitize_text_field(name, MAX_NAME_LENGTH, "Nom")

    if prenom is not None:
        result['prenom'] = sanitize_text_field(prenom, MAX_NAME_LENGTH, "Prénom")

    if entreprise is not None:
        result['entreprise'] = sanitize_text_field(entreprise, MAX_NAME_LENGTH, "Entreprise")

    return result
