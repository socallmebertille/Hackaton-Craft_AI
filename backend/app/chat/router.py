"""
Router API pour l'orchestration des messages IA
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database.base import get_db
from app.database.models import User, Chat, Message as DBMessage
from app.auth.dependencies import get_current_active_user
from app.chat.orchestrator import AIOrchestrator
from app.core.sanitizer import sanitize_message


router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    """Modèle de requête pour envoyer un message"""
    chat_id: str  # UUID au format string
    content: str = Field(..., min_length=1, max_length=10000, description="Contenu du message")

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Sanitize message content to prevent XSS"""
        return sanitize_message(v)


class MessageResponse(BaseModel):
    """Modèle de réponse pour un message"""
    success: bool
    message_id: Optional[str] = None  # UUID au format string
    response: Optional[str] = None
    intention: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    end_conversation: bool = False
    error: Optional[str] = None


@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Envoie un message et obtient une réponse de l'IA

    Le message passe par l'orchestrateur qui :
    1. Analyse l'intention (Pipeline 0)
    2. Route vers le bon pipeline
    3. Retourne la réponse appropriée
    """

    # Vérifier que le chat existe et appartient à l'utilisateur
    chat = db.query(Chat).filter(
        Chat.id == request.chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat non trouvé"
        )

    # Vérifier qu'aucun message utilisateur n'existe déjà (un seul message par chat autorisé)
    existing_user_message = db.query(DBMessage).filter(
        DBMessage.chat_id == chat.id,
        DBMessage.role == "user"
    ).first()

    if existing_user_message:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un message a déjà été envoyé dans ce chat. Veuillez créer un nouveau chat."
        )

    # Calculer le prochain numéro de message
    max_numero = db.query(func.max(DBMessage.numero)).filter(
        DBMessage.chat_id == chat.id
    ).scalar() or 0
    next_numero = max_numero + 1

    # Sauvegarder le message de l'utilisateur
    user_message = DBMessage(
        chat_id=chat.id,
        numero=next_numero,
        role="user",
        content={"message": request.content}  # Stocker en JSON
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    try:
        # Traiter le message via l'orchestrateur
        orchestrator = AIOrchestrator()
        result = await orchestrator.process_message(
            message=request.content,
            user_id=current_user.id,
            chat_id=chat.id
        )

        # Si erreur lors du traitement
        if not result.get("success"):
            return MessageResponse(
                success=False,
                error=result.get("error", "Erreur inconnue"),
                end_conversation=False
            )

        # Gérer les messages multiples pour les débats
        if result.get("debate_messages"):
            # Débat : créer plusieurs messages
            current_numero = next_numero + 1
            first_message_id = None

            for message_text in result["debate_messages"]:
                assistant_content = {
                    "response": message_text,
                    "intention": result.get("intention"),
                    "confidence": result.get("confidence")
                }

                assistant_message = DBMessage(
                    chat_id=chat.id,
                    numero=current_numero,
                    role="assistant",
                    content=assistant_content
                )
                db.add(assistant_message)
                current_numero += 1

                if first_message_id is None:
                    db.flush()  # Pour obtenir l'ID
                    first_message_id = str(assistant_message.id)

            # Mettre à jour le titre du chat si c'est le premier message
            if next_numero == 1:
                chat.titre = request.content[:50] + ("..." if len(request.content) > 50 else "")

            db.commit()

            return MessageResponse(
                success=True,
                message_id=first_message_id,
                response=f"{len(result['debate_messages'])} messages de débat envoyés",
                intention=result.get("intention"),
                confidence=result.get("confidence"),
                reasoning=result.get("reasoning"),
                end_conversation=result.get("end_conversation", False)
            )
        else:
            # Cas normal : un seul message
            assistant_content = {
                "response": result.get("response", ""),
                "intention": result.get("intention"),
                "confidence": result.get("confidence"),
                "reasoning": result.get("reasoning")
            }

            # Ajouter les données spécifiques selon le type de réponse
            if result.get("debate"):
                assistant_content["debate"] = result["debate"]
            if result.get("citations"):
                assistant_content["citations"] = result["citations"]

            assistant_message = DBMessage(
                chat_id=chat.id,
                numero=next_numero + 1,
                role="assistant",
                content=assistant_content
            )
            db.add(assistant_message)

            # Mettre à jour le titre du chat si c'est le premier message
            if next_numero == 1:
                # Générer un titre basé sur le premier message
                chat.titre = request.content[:50] + ("..." if len(request.content) > 50 else "")

            db.commit()
            db.refresh(assistant_message)

            return MessageResponse(
                success=True,
                message_id=str(assistant_message.id),
                response=result.get("response"),
                intention=result.get("intention"),
                confidence=result.get("confidence"),
                reasoning=result.get("reasoning"),
                end_conversation=result.get("end_conversation", False)
            )

    except Exception as e:
        print(f"[Router] Erreur lors du traitement du message: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement du message: {str(e)}"
        )


@router.post("/new")
async def create_new_chat(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau chat pour l'utilisateur
    """
    new_chat = Chat(
        user_id=current_user.id,
        titre="Nouvelle conversation"
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return {
        "success": True,
        "chat_id": str(new_chat.id),  # Convertir UUID en string
        "title": new_chat.titre
    }


@router.get("/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les messages d'un chat
    """
    # Vérifier que le chat existe et appartient à l'utilisateur
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat non trouvé"
        )

    messages = db.query(DBMessage).filter(
        DBMessage.chat_id == chat_id
    ).order_by(DBMessage.date_creation.asc()).all()

    return {
        "success": True,
        "chat_id": chat_id,
        "title": chat.titre,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.date_creation.isoformat()
            }
            for msg in messages
        ]
    }


@router.get("/list")
async def get_user_chats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les chats de l'utilisateur
    """
    chats = db.query(Chat).filter(
        Chat.user_id == current_user.id
    ).order_by(Chat.derniere_utilisation.desc()).all()

    return {
        "success": True,
        "chats": [
            {
                "id": str(chat.id),
                "title": chat.titre,
                "messages_count": len(chat.messages),
                "created_at": chat.date_creation.isoformat(),
                "updated_at": chat.derniere_utilisation.isoformat()
            }
            for chat in chats
        ]
    }
