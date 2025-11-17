"""
Modèles SQLAlchemy pour la base de données
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """Modèle utilisateur"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    # GDPR consent fields
    cgu_accepted = Column(Boolean, nullable=False, default=False, server_default="false")
    privacy_policy_accepted = Column(Boolean, nullable=False, default=False, server_default="false")
    consent_date = Column(TIMESTAMP, nullable=True)

    # Account deletion (GDPR right to deletion)
    account_deletion_requested = Column(Boolean, default=False, server_default="false")
    deletion_request_date = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        CheckConstraint('role IN (0, 1, 2)', name='check_role_values'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"

    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire (sans le password_hash)"""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "cgu_accepted": self.cgu_accepted,
            "privacy_policy_accepted": self.privacy_policy_accepted,
            "consent_date": self.consent_date.isoformat() if self.consent_date else None,
            "account_deletion_requested": self.account_deletion_requested,
            "deletion_request_date": self.deletion_request_date.isoformat() if self.deletion_request_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_role_name(self) -> str:
        """Retourne le nom du rôle"""
        roles = {0: "En attente", 1: "Utilisateur", 2: "Admin"}
        return roles.get(self.role, "Inconnu")
