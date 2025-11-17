"""
Services métier pour la feature Auth
"""
from utils import create_access_token


def create_token(user_id: int, email: str, role: int) -> str:
    """Génère un JWT token pour un utilisateur"""
    token_data = {
        "user_id": user_id,
        "email": email,
        "role": role
    }
    return create_access_token(token_data)
