"""
Routes API pour la feature User (gestion du profil)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db, verify_password, hash_password, User
from features.auth.dependencies import get_current_user
from .schemas import UpdateProfileRequest, UpdatePasswordRequest, AccountDeletionRequest


router = APIRouter(prefix="/api/user", tags=["user"])


@router.put('/profile')
async def update_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Met à jour le profil utilisateur (réservé pour futures modifications)"""

    # Aucun champ éditable pour le moment
    # Cette route est conservée pour compatibilité future

    db.commit()
    db.refresh(user)

    return {
        'message': 'Profil mis à jour avec succès',
        'user': user.to_dict()
    }


@router.put('/password')
async def update_password(
    payload: UpdatePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Modifie le mot de passe de l'utilisateur"""

    # Vérifier l'ancien mot de passe
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail='Mot de passe actuel incorrect')

    # Hasher et enregistrer le nouveau mot de passe
    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {
        'message': 'Mot de passe mis à jour avec succès'
    }


@router.post('/request-deletion')
async def request_account_deletion(
    payload: AccountDeletionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Demande la suppression du compte (RGPD - droit à l'effacement)"""

    # Vérifier le mot de passe pour confirmer l'identité
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail='Mot de passe incorrect')

    # Vérifier la confirmation
    if not payload.confirmation:
        raise HTTPException(status_code=400, detail='Vous devez confirmer la suppression')

    # Marquer le compte pour suppression
    user.account_deletion_requested = True
    user.deletion_request_date = datetime.utcnow()
    db.commit()

    return {
        'message': 'Demande de suppression enregistrée. Votre compte sera supprimé sous 30 jours. Vous pouvez annuler cette demande en vous reconnectant.',
        'deletion_request_date': user.deletion_request_date.isoformat()
    }


@router.post('/cancel-deletion')
async def cancel_account_deletion(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Annule la demande de suppression du compte"""

    if not user.account_deletion_requested:
        raise HTTPException(status_code=400, detail='Aucune demande de suppression en cours')

    # Annuler la demande
    user.account_deletion_requested = False
    user.deletion_request_date = None
    db.commit()

    return {
        'message': 'Demande de suppression annulée avec succès'
    }


@router.delete('/account')
async def delete_account(
    payload: AccountDeletionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Supprime définitivement le compte utilisateur (RGPD - droit à l'effacement)"""

    # Vérifier le mot de passe pour confirmer l'identité
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail='Mot de passe incorrect')

    # Vérifier la confirmation
    if not payload.confirmation:
        raise HTTPException(status_code=400, detail='Vous devez confirmer la suppression')

    # Supprimer définitivement l'utilisateur
    user_email = user.email
    db.delete(user)
    db.commit()

    return {
        'message': f'Compte {user_email} supprimé définitivement conformément au RGPD'
    }
