"""
Routes API pour la feature Admin (panel d'administration)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from db import get_db, User
from features.auth.dependencies import require_admin


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get('/users')
async def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Liste tous les utilisateurs - Admin uniquement"""

    users = db.query(User).order_by(User.created_at.desc()).all()

    return {
        'users': [
            {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'role_name': user.get_role_name(),
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
    }


@router.get('/users/pending')
async def list_pending_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Liste les utilisateurs en attente de validation (role=0) - Admin uniquement"""

    pending_users = db.query(User).filter(User.role == 0).order_by(User.created_at.desc()).all()

    return {
        'users': [
            {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            for user in pending_users
        ]
    }


@router.get('/users/validated')
async def list_validated_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Liste les utilisateurs validés (role=1) - Admin uniquement"""

    validated_users = db.query(User).filter(User.role == 1).order_by(User.created_at.desc()).all()

    return {
        'users': [
            {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            for user in validated_users
        ]
    }


@router.post('/users/{user_id}/validate')
async def validate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Valide un utilisateur en attente (passe de role=0 à role=1) - Admin uniquement"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='Utilisateur non trouvé')

    if user.role != 0:
        raise HTTPException(status_code=400, detail='Cet utilisateur n\'est pas en attente de validation')

    user.role = 1
    db.commit()
    db.refresh(user)

    return {
        'message': f'Utilisateur {user.email} validé avec succès',
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'role_name': user.get_role_name()
        }
    }


@router.delete('/users/{user_id}')
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Supprime un utilisateur - Admin uniquement"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='Utilisateur non trouvé')

    if user.role == 2:
        raise HTTPException(status_code=400, detail='Impossible de supprimer un compte administrateur')

    db.delete(user)
    db.commit()

    return {
        'message': f'Utilisateur {user.email} supprimé avec succès'
    }
