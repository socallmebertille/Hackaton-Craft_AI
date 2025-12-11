"""
Routes d'administration - Gestion des utilisateurs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.base import get_db
from app.database.models import User
from app.auth import schemas, dependencies
from app.core.email import send_email, generate_account_approved_email
from typing import Optional
import uuid

router = APIRouter(
    prefix="/api/admin",
    tags=["Administration"]
)


def check_moderator_limit(db: Session, moderator: User, company: str) -> bool:
    """
    Vérifie si le modérateur a atteint sa limite d'utilisateurs actifs
    """
    if not moderator.is_moderator or moderator.moderator_company != company:
        return False

    if moderator.max_users is None:
        return True  # Pas de limite

    # Compter les utilisateurs actifs de cette entreprise
    active_count = db.query(func.count(User.id)).filter(
        User.entreprise == company,
        User.is_active == True,
        User.id != moderator.id  # Ne pas compter le modérateur lui-même
    ).scalar()

    return active_count < moderator.max_users


@router.get("/users", response_model=schemas.UserListResponse)
async def get_users(
    status_filter: Optional[str] = None,  # "pending", "active", "all"
    company: Optional[str] = None,
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste les utilisateurs
    - Admin: peut voir tous les utilisateurs
    - Modérateur: peut voir uniquement les utilisateurs de son entreprise
    """
    if not (current_user.is_admin or current_user.is_moderator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    # Base query
    query = db.query(User)

    # Si modérateur, filtrer par entreprise
    if current_user.is_moderator and not current_user.is_admin:
        query = query.filter(User.entreprise == current_user.moderator_company)
    elif company:  # Admin peut filtrer par entreprise
        query = query.filter(User.entreprise == company)

    # Filtrer par statut
    if status_filter == "pending":
        query = query.filter(User.is_active == False, User.email_verified == True)
    elif status_filter == "active":
        query = query.filter(User.is_active == True)

    users = query.all()
    total = len(users)

    # Compter les utilisateurs en attente
    pending_query = db.query(func.count(User.id)).filter(
        User.is_active == False,
        User.email_verified == True
    )
    if current_user.is_moderator and not current_user.is_admin:
        pending_query = pending_query.filter(User.entreprise == current_user.moderator_company)

    pending = pending_query.scalar()

    return schemas.UserListResponse(
        users=[schemas.UserResponse.model_validate(u) for u in users],
        total=total,
        pending=pending
    )


@router.patch("/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_update: schemas.UserUpdate,
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour un utilisateur
    - Admin: peut tout modifier
    - Modérateur: peut activer/désactiver les utilisateurs de son entreprise
    """
    if not (current_user.is_admin or current_user.is_moderator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    # Récupérer l'utilisateur à modifier
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Vérifier les permissions du modérateur
    if current_user.is_moderator and not current_user.is_admin:
        # Le modérateur ne peut modifier que les utilisateurs de son entreprise
        if user.entreprise != current_user.moderator_company:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez gérer que les utilisateurs de votre entreprise"
            )

        # Le modérateur ne peut modifier que is_active
        if user_update.is_moderator is not None or user_update.moderator_company is not None or user_update.max_users is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas la permission de modifier ces champs"
            )

        # Vérifier la limite si activation d'un utilisateur
        if user_update.is_active is True and not user.is_active:
            if not check_moderator_limit(db, current_user, user.entreprise):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Limite de {current_user.max_users} utilisateurs atteinte pour votre entreprise"
                )

    # Vérifier si on active le compte (pour envoyer l'email)
    was_inactive = not user.is_active
    is_being_activated = user_update.is_active is True and was_inactive

    # Appliquer les modifications
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    # Seul l'admin peut modifier ces champs
    if current_user.is_admin:
        if user_update.is_moderator is not None:
            user.is_moderator = user_update.is_moderator
        if user_update.moderator_company is not None:
            user.moderator_company = user_update.moderator_company
        if user_update.max_users is not None:
            user.max_users = user_update.max_users

    db.commit()
    db.refresh(user)

    # Envoyer l'email d'approbation si le compte vient d'être activé
    if is_being_activated:
        try:
            html_content, text_content = generate_account_approved_email(user.prenom, user.nom)
            await send_email(
                to_emails=[user.email],
                subject="Votre compte Juridique AI a été approuvé",
                html_content=html_content,
                text_content=text_content
            )
        except Exception as e:
            # Ne pas bloquer la validation si l'email échoue
            print(f"⚠️ Erreur lors de l'envoi de l'email d'approbation: {e}")

    return schemas.UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un utilisateur
    - Admin: peut supprimer n'importe qui
    - Modérateur: peut supprimer les utilisateurs de son entreprise
    """
    if not (current_user.is_admin or current_user.is_moderator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    # Récupérer l'utilisateur à supprimer
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Empêcher la suppression d'un admin
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de supprimer un administrateur"
        )

    # Vérifier les permissions du modérateur
    if current_user.is_moderator and not current_user.is_admin:
        if user.entreprise != current_user.moderator_company:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez supprimer que les utilisateurs de votre entreprise"
            )

    db.delete(user)
    db.commit()

    return {"message": "Utilisateur supprimé avec succès"}


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Statistiques pour l'admin/modérateur
    """
    if not (current_user.is_admin or current_user.is_moderator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    # Base query
    if current_user.is_moderator and not current_user.is_admin:
        company_filter = User.entreprise == current_user.moderator_company
        total_users = db.query(func.count(User.id)).filter(company_filter).scalar()
        active_users = db.query(func.count(User.id)).filter(company_filter, User.is_active == True).scalar()
        pending_users = db.query(func.count(User.id)).filter(
            company_filter,
            User.is_active == False,
            User.email_verified == True
        ).scalar()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_users": pending_users,
            "max_users": current_user.max_users,
            "company": current_user.moderator_company
        }
    else:  # Admin
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        pending_users = db.query(func.count(User.id)).filter(
            User.is_active == False,
            User.email_verified == True
        ).scalar()
        moderators = db.query(func.count(User.id)).filter(User.is_moderator == True).scalar()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_users": pending_users,
            "moderators": moderators
        }
