"""
Routes API pour la feature Debate (débats juridiques)
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from db import get_db, User
from features.auth.dependencies import get_current_user
from .schemas import QuestionRequest, DebateResponse, DebateResult
from .storage import debates_storage
from .service import run_debate_background
from .pdf_utils import generate_debate_pdf


router = APIRouter(prefix="/api/debate", tags=["debate"])


@router.post("/submit", response_model=DebateResponse)
async def submit_question(
    request: QuestionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Soumet une question juridique et lance un débat contradictoire
    Nécessite un utilisateur validé (role >= 1)

    Cet endpoint:
    1. Vérifie que l'utilisateur est authentifié et validé
    2. Valide la question (min 10 caractères)
    3. Génère un ID unique pour le débat
    4. Lance le débat en arrière-plan (non-bloquant)
    5. Retourne immédiatement l'ID pour polling

    Le traitement en arrière-plan évite de bloquer l'API pendant
    plusieurs minutes (temps de génération des arguments).

    Args:
        request (QuestionRequest): Contient la question juridique
        background_tasks (BackgroundTasks): Gestionnaire de tâches FastAPI
        db (Session): Session de base de données
        user (User): Utilisateur courant (injecté par dépendance)

    Returns:
        DebateResponse: ID du débat et confirmation de lancement

    Raises:
        HTTPException 403: Si l'utilisateur n'est pas validé (role < 1)

    Example:
        POST /api/debate/submit
        Headers: {"Authorization": "Bearer <token>"}
        Body: {"question": "Un CDD peut-il être renouvelé indéfiniment?"}
        Response: {
            "debate_id": "a3f8c7b2-...",
            "status": "pending",
            "message": "Débat lancé en arrière-plan"
        }
    """
    # Vérifier que l'utilisateur est validé (role >= 1)
    if user.role < 1:
        raise HTTPException(
            status_code=403,
            detail='Votre compte doit être validé par un administrateur pour utiliser cette fonctionnalité'
        )

    # Note: La validation est déjà faite par le modèle Pydantic (QuestionRequest)
    # avec le validator 'validate_question' qui:
    # - Vérifie la longueur min/max
    # - Détecte les injections de prompt
    # - Nettoie le contenu (sanitization)
    # Si cette ligne est atteinte, la question est déjà validée et sécurisée

    # Générer un UUID v4 unique pour identifier ce débat
    debate_id = str(uuid.uuid4())

    # Initialiser l'entrée dans le stockage avec statut "pending"
    debates_storage[debate_id] = {
        "debate_id": debate_id,
        "status": "pending",              # Statut initial
        "progress": "En attente de démarrage...",
        "question": request.question,
        "legal_context": None,            # Sera rempli pendant le traitement
        "debate_rounds": None,            # Sera rempli pendant le traitement
        "summary": None,                  # Sera rempli à la fin
        "created_at": datetime.now().isoformat(),
        "completed_at": None,             # Sera rempli à la fin/erreur
        "error": None,                    # Stocke le message d'erreur si échec
        "user_id": user.id                # Associer le débat à l'utilisateur
    }

    # Ajouter la tâche de débat à la queue de BackgroundTasks
    # Cette tâche s'exécutera après le retour de la réponse
    background_tasks.add_task(run_debate_background, debate_id, request.question)

    # Retourner immédiatement l'ID (le client pourra poller le statut)
    return DebateResponse(
        debate_id=debate_id,
        status="pending",
        message="Débat lancé en arrière-plan"
    )


@router.get("/{debate_id}", response_model=DebateResult)
async def get_debate_status(
    debate_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Récupère l'état et les résultats d'un débat (endpoint de polling)

    Cet endpoint est appelé régulièrement par le frontend pour :
    - Vérifier si le débat est toujours en cours ("pending" ou "processing")
    - Récupérer les résultats quand il est terminé ("completed")
    - Détecter les erreurs éventuelles ("error")

    Args:
        debate_id (str): UUID du débat à consulter
        db (Session): Session de base de données
        user (User): Utilisateur courant (vérifié par authentification)

    Returns:
        DebateResult: État complet du débat avec tous les champs remplis

    Raises:
        HTTPException 404: Si l'ID n'existe pas dans le stockage

    Example:
        GET /api/debate/a3f8c7b2-1234-...
        Headers: {"Authorization": "Bearer <token>"}
        Response (si en cours): {
            "debate_id": "a3f8c7b2-...",
            "status": "processing",
            "question": "...",
            "legal_context": null,
            "debate_rounds": null,
            ...
        }
        Response (si terminé): {
            "status": "completed",
            "legal_context": {...},
            "debate_rounds": [...],
            "summary": "...",
            ...
        }
    """
    # Vérifier que le débat existe
    if debate_id not in debates_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Débat {debate_id} introuvable"
        )

    # Récupérer les données du débat
    debate = debates_storage[debate_id]

    # Retourner le résultat formaté selon le schéma Pydantic
    return DebateResult(
        debate_id=debate["debate_id"],
        status=debate["status"],
        question=debate["question"],
        legal_context=debate.get("legal_context"),
        debate_rounds=debate.get("debate_rounds"),
        summary=debate.get("summary"),
        created_at=debate["created_at"],
        completed_at=debate.get("completed_at")
    )


@router.get("/{debate_id}/export-pdf")
async def export_debate_to_pdf(
    debate_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Exporte un débat terminé au format PDF professionnel

    Génère un document PDF bien formaté avec:
    - En-tête avec titre et date
    - Question juridique mise en évidence
    - Arguments du débat clairement structurés
    - Synthèse finale
    - Mise en page professionnelle avec styles

    Args:
        debate_id (str): UUID du débat à exporter

    Returns:
        Response: Fichier PDF en téléchargement direct

    Raises:
        HTTPException 404: Si le débat n'existe pas
        HTTPException 400: Si le débat n'est pas terminé
    """
    # Vérifier que le débat existe
    if debate_id not in debates_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Débat {debate_id} introuvable"
        )

    debate = debates_storage[debate_id]

    # Vérifier que le débat est terminé
    if debate["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Le débat doit être terminé pour être exporté en PDF"
        )

    try:
        return generate_debate_pdf(debate)
    except Exception as e:
        print(f"[API] Erreur lors de l'export PDF {debate_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )


# Route pour lister tous les débats (compatible avec l'ancien /api/debates)
@router.get("s")  # Cela crée la route /api/debates
async def list_debates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Liste tous les débats (en cours et terminés)

    Retourne un résumé de tous les débats pour affichage dans
    une interface de type historique/dashboard.

    Returns:
        Dict: Contient une liste "debates" avec les infos essentielles
              de chaque débat (sans le contenu complet pour alléger)

    Example:
        GET /api/debates
        Response: {
            "debates": [
                {
                    "debate_id": "abc-123...",
                    "question": "Validité d'un CDD?",
                    "status": "completed",
                    "created_at": "2024-10-14T10:30:00"
                },
                {
                    "debate_id": "def-456...",
                    "question": "Licenciement pour faute?",
                    "status": "processing",
                    "created_at": "2024-10-14T11:15:00"
                }
            ]
        }
    """
    return {
        "debates": [
            {
                "debate_id": d["debate_id"],
                "question": d["question"],
                "status": d["status"],
                "created_at": d["created_at"]
            }
            for d in debates_storage.values()
        ]
    }


@router.delete("/{debate_id}")
async def delete_debate(
    debate_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Supprime un débat du stockage

    Permet de nettoyer les débats terminés ou annulés.
    En production avec une DB, ceci pourrait être un soft-delete.

    Args:
        debate_id (str): UUID du débat à supprimer

    Returns:
        Dict: Message de confirmation

    Raises:
        HTTPException 404: Si le débat n'existe pas

    Example:
        DELETE /api/debate/abc-123...
        Response: {
            "message": "Débat abc-123... supprimé avec succès"
        }
    """
    # Vérifier que le débat existe avant de le supprimer
    if debate_id not in debates_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Débat {debate_id} introuvable"
        )

    # Supprimer du dictionnaire
    del debates_storage[debate_id]

    return {"message": f"Débat {debate_id} supprimé avec succès"}
