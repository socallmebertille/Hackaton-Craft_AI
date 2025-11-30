"""
Schemas Pydantic pour l'authentification
Validation des données entrantes/sortantes
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid


class UserRegister(BaseModel):
    """Schema pour l'inscription d'un utilisateur"""
    prenom: str = Field(..., min_length=1, max_length=100, description="Prénom de l'utilisateur")
    nom: str = Field(..., min_length=1, max_length=100, description="Nom de l'utilisateur")
    entreprise: str = Field(..., min_length=1, max_length=200, description="Nom de l'entreprise")
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    password: str = Field(..., min_length=8, max_length=100, description="Mot de passe (min 8 caractères)")

    class Config:
        json_schema_extra = {
            "example": {
                "prenom": "Jean",
                "nom": "Dupont",
                "entreprise": "MIBS SARL",
                "email": "jean.dupont@mibs.com",
                "password": "SecurePassword123"
            }
        }


class UserLogin(BaseModel):
    """Schema pour la connexion d'un utilisateur"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "jean.dupont@mibs.com",
                "password": "SecurePassword123"
            }
        }


class Token(BaseModel):
    """Schema pour le token JWT"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema pour les données contenues dans le token"""
    user_id: Optional[uuid.UUID] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """Schema pour la réponse utilisateur (sans le password)"""
    id: uuid.UUID
    prenom: str
    nom: str
    entreprise: str
    email: str
    date_creation: datetime
    is_active: bool
    is_admin: bool = False
    is_moderator: bool = False
    moderator_company: Optional[str] = None
    max_users: Optional[int] = None
    email_verified: bool = False

    class Config:
        from_attributes = True  # Pour compatibilité avec SQLAlchemy models


class UserUpdate(BaseModel):
    """Schema pour la mise à jour d'un utilisateur par admin/modérateur"""
    is_active: Optional[bool] = None
    is_moderator: Optional[bool] = None
    moderator_company: Optional[str] = None
    max_users: Optional[int] = None


class UserListResponse(BaseModel):
    """Schema pour la liste des utilisateurs"""
    users: list[UserResponse]
    total: int
    pending: int  # Nombre d'utilisateurs en attente


class TokenWithUser(BaseModel):
    """Schema pour le token JWT avec les informations utilisateur"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
