"""
Schémas Pydantic pour la feature User
"""
from typing import Optional
from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    # Aucun champ éditable pour le moment
    # Conservé pour compatibilité future
    pass


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class AccountDeletionRequest(BaseModel):
    password: str
    confirmation: bool = Field(..., description="User must confirm deletion")
