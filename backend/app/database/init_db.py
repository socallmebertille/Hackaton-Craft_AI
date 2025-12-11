"""
Script d'initialisation de la base de données
Crée toutes les tables et peut créer un utilisateur admin de test
"""

from app.database.base import Base, engine, SessionLocal
from app.database.models import User, Chat, Message
from app.core.config import settings
from app.core.security import get_password_hash


def create_admin_user():
    """
    Crée le compte administrateur si les variables d'environnement sont configurées
    et que le compte n'existe pas déjà
    """
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        print("⚠️  Variables ADMIN_EMAIL et ADMIN_PASSWORD non configurées - Aucun admin créé")
        return

    # Vérifier la longueur du mot de passe admin (limite bcrypt : 72 octets)
    password_bytes = settings.ADMIN_PASSWORD.encode('utf-8')
    if len(password_bytes) > 72:
        print(f"❌ Erreur: Mot de passe ADMIN_PASSWORD trop long")
        print(f"   Longueur actuelle: {len(password_bytes)} octets")
        print(f"   Maximum autorisé: 72 octets (limitation bcrypt)")
        print(f"   Veuillez raccourcir le mot de passe dans le fichier .env")
        return

    db = SessionLocal()
    try:
        # Vérifier si l'admin existe déjà
        existing_admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()

        if existing_admin:
            print(f"✅ Compte administrateur existe déjà: {settings.ADMIN_EMAIL}")
            # S'assurer que le compte a les droits admin
            if not existing_admin.is_admin:
                existing_admin.is_admin = True
                db.commit()
                print(f"   → Droits administrateur accordés")
            if not existing_admin.email_verified:
                existing_admin.email_verified = True
                db.commit()
                print(f"   → Email vérifié automatiquement")
            if not existing_admin.is_active:
                existing_admin.is_active = True
                db.commit()
                print(f"   → Compte activé")
            return

        # Créer le compte administrateur
        admin_user = User(
            prenom=settings.ADMIN_PRENOM,
            nom=settings.ADMIN_NOM,
            entreprise=settings.ADMIN_ENTREPRISE,
            email=settings.ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            is_active=True,
            is_admin=True,
            email_verified=True,  # Admin vérifié automatiquement
            verification_token=None,
            verification_token_expires=None
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"✅ Compte administrateur créé avec succès:")
        print(f"   Email: {settings.ADMIN_EMAIL}")
        print(f"   Nom: {settings.ADMIN_PRENOM} {settings.ADMIN_NOM}")
        print(f"   Entreprise: {settings.ADMIN_ENTREPRISE}")
        print(f"   ⚠️  N'oubliez pas de changer le mot de passe admin en production!")

    except Exception as e:
        print(f"❌ Erreur lors de la création du compte admin: {str(e)}")
        db.rollback()
    finally:
        db.close()


def init_db():
    """
    Crée toutes les tables dans la base de données
    """
    print(f"🗄️  Initialisation de la base de données...")
    print(f"📍 Database URL: {settings.DATABASE_URL}")

    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)

    print("✅ Tables créées avec succès:")
    print(f"   - users")
    print(f"   - chats")
    print(f"   - messages")

    # Créer le compte administrateur
    print(f"\n👤 Vérification du compte administrateur...")
    create_admin_user()


def drop_db():
    """
    Supprime toutes les tables (ATTENTION: Perte de données)
    """
    print("⚠️  Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables supprimées")


def reset_db():
    """
    Réinitialise complètement la base de données
    """
    print("🔄 Réinitialisation de la base de données...")
    drop_db()
    init_db()
    print("✅ Base de données réinitialisée")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            init_db()
        elif command == "drop":
            drop_db()
        elif command == "reset":
            reset_db()
        else:
            print(f"❌ Commande inconnue: {command}")
            print("Usage: python -m app.database.init_db [init|drop|reset]")
    else:
        # Par défaut, initialiser
        init_db()
