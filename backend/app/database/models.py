"""
Models SQLAlchemy - Définition des tables de la base de données
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class User(Base):
    """
    Table users - Utilisateurs de l'application
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prenom = Column(String(100), nullable=False)
    nom = Column(String(100), nullable=False)
    entreprise = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)  # False par défaut, en attente de validation
    is_admin = Column(Boolean, default=False, nullable=False)

    # Modérateur
    is_moderator = Column(Boolean, default=False, nullable=False)
    moderator_company = Column(String(200), nullable=True)  # Entreprise dont il est modérateur
    max_users = Column(Integer, nullable=True)  # Nombre max d'utilisateurs autorisés pour ce modérateur

    # Vérification email
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True, unique=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)

    # Relations
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Chat(Base):
    """
    Table chats - Conversations/chats des utilisateurs
    Supprimés automatiquement après 24h d'inactivité
    """
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    titre = Column(String(500), nullable=True)  # Titre du chat (peut être généré auto)
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False)
    derniere_utilisation = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relations
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.numero")

    # Index pour la suppression automatique
    __table_args__ = (
        Index('ix_chats_derniere_utilisation_active', 'derniere_utilisation', 'is_active'),
    )

    def __repr__(self):
        return f"<Chat {self.id} - {self.titre[:30] if self.titre else 'Sans titre'}>"


class Message(Base):
    """
    Table messages - Messages d'un chat
    Numérotés séquentiellement (1, 2, 3...) par chat
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    numero = Column(Integer, nullable=False)  # Numéro séquentiel dans le chat
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'pour', 'contre', 'summary'
    content = Column(JSONB, nullable=False)  # Contenu du message en JSON
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    chat = relationship("Chat", back_populates="messages")

    # Index pour performance
    __table_args__ = (
        Index('ix_messages_chat_numero', 'chat_id', 'numero'),
    )

    def __repr__(self):
        return f"<Message {self.chat_id} #{self.numero} - {self.role}>"
