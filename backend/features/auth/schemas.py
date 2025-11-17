"""
Schémas Pydantic pour la feature Auth
"""
from pydantic import BaseModel, Field, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    cgu_accepted: bool = Field(..., description="CGU acceptance required")
    privacy_policy_accepted: bool = Field(..., description="Privacy policy acceptance required")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
