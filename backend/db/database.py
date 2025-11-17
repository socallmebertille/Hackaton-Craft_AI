"""
Configuration de la base de données et initialisation
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt
from pathlib import Path

# Configuration de la base de données
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Créer l'engine SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency pour obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def run_migrations():
    """Exécute tous les fichiers SQL de migration dans l'ordre"""
    migrations_dir = Path(__file__).parent / 'migrations'

    if not migrations_dir.exists():
        print("⚠️  Aucun dossier de migrations trouvé")
        return

    # Récupérer tous les fichiers .sql et les trier
    sql_files = sorted(migrations_dir.glob('*.sql'))

    if not sql_files:
        print("⚠️  Aucun fichier de migration trouvé")
        return

    print(f"\n🔄 Exécution des migrations ({len(sql_files)} fichier(s))...\n")

    with engine.connect() as connection:
        for sql_file in sql_files:
            print(f"  ▸ Exécution de {sql_file.name}...")
            try:
                sql_content = sql_file.read_text(encoding='utf-8')
                connection.execute(text(sql_content))
                connection.commit()
                print(f"    ✅ {sql_file.name} exécuté avec succès")
            except Exception as e:
                print(f"    ❌ Erreur lors de l'exécution de {sql_file.name}: {e}")
                raise

    print("\n✅ Toutes les migrations ont été exécutées avec succès\n")


def create_admin_if_not_exists():
    """Crée un utilisateur admin par défaut si aucun admin n'existe"""
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_email or not admin_password:
        print("⚠️  ADMIN_EMAIL ou ADMIN_PASSWORD non défini dans .env")
        return

    with engine.connect() as connection:
        # Vérifier si un admin existe déjà
        result = connection.execute(
            text("SELECT COUNT(*) FROM users WHERE role = 2")
        )
        admin_count = result.scalar()

        if admin_count > 0:
            print(f"ℹ️  Un admin existe déjà ({admin_count} admin(s) trouvé(s))")
            return

        # Créer l'admin
        print(f"\n👤 Création de l'utilisateur admin: {admin_email}")
        password_hash = hash_password(admin_password)

        connection.execute(
            text("""
                INSERT INTO users (email, password_hash, role)
                VALUES (:email, :password_hash, :role)
            """),
            {
                "email": admin_email,
                "password_hash": password_hash,
                "role": 2
            }
        )
        connection.commit()
        print(f"✅ Admin créé avec succès: {admin_email}\n")


def init_database():
    """
    Initialise la base de données:
    1. Exécute les migrations
    2. Crée un admin par défaut si nécessaire
    """
    print("\n" + "="*60)
    print("🚀 INITIALISATION DE LA BASE DE DONNÉES")
    print("="*60)

    try:
        # Tester la connexion
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Connexion à la base de données réussie")

        # Exécuter les migrations
        run_migrations()

        # Créer l'admin par défaut
        create_admin_if_not_exists()

        print("="*60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ ERREUR lors de l'initialisation de la base de données:")
        print(f"   {e}\n")
        raise
