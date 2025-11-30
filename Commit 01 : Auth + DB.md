# Commit 01 : Authentification + Base de données

## Vue d'ensemble

Ce commit implémente un système complet d'authentification avec gestion des utilisateurs, système de rôles (Admin/Modérateur/Utilisateur), et sécurité renforcée contre les injections SQL et XSS.

---

## 🎯 Fonctionnalités principales

### 1. Système d'authentification complet

#### Backend (FastAPI)
- **Inscription utilisateur** avec validation email
- **Connexion** avec JWT tokens
- **Vérification email** via lien SMTP
- **Protection des routes** avec middlewares JWT
- **Gestion de session** persistante

#### Frontend (React)
- **Pages** : Home, Admin Panel, Admin Dev, Verify Email
- **Composants** : Header commun, LoginModal, RegisterModal
- **Authentification persistante** avec localStorage
- **Redirection automatique** selon les rôles

---

### 2. Système de rôles et permissions

#### Trois niveaux d'accès :

**👤 Utilisateur**
- Compte créé mais inactif par défaut
- Doit vérifier son email
- Doit être approuvé par admin/modérateur

**🛡️ Modérateur**
- Gère les utilisateurs de son entreprise uniquement
- Peut accepter/refuser/désactiver les utilisateurs
- Limité par un quota `max_users` défini par l'admin
- Ne peut pas supprimer les admins

**👑 Administrateur**
- Accès complet à tous les utilisateurs
- Peut nommer/retirer des modérateurs
- Peut gérer toutes les entreprises
- Accès au Dev Panel
- Compte créé automatiquement via variables d'environnement

---

### 3. Workflow d'inscription et validation

```
1. Utilisateur s'inscrit
   ↓
2. Email de vérification envoyé (SMTP)
   ↓
3. Utilisateur clique sur le lien → email_verified = True
   ↓
4. Admin/Modérateur approuve → is_active = True
   ↓
5. Email d'approbation envoyé
   ↓
6. Utilisateur peut se connecter
```

---

### 4. Base de données PostgreSQL

#### Modèle User
```python
- id: UUID (PK)
- email: String(255) unique
- hashed_password: String(255)
- prenom: String(100)
- nom: String(100)
- entreprise: String(200)
- date_creation: DateTime
- is_active: Boolean (défaut: False)
- email_verified: Boolean (défaut: False)
- verification_token: String(255)
- verification_token_expires: DateTime
- is_admin: Boolean (défaut: False)
- is_moderator: Boolean (défaut: False)
- moderator_company: String(200) nullable
- max_users: Integer nullable
```

#### Modèle Chat
```python
- id: UUID (PK)
- user_id: UUID (FK → User)
- titre: String(255)
- date_creation: DateTime
- date_modification: DateTime
```

---

## 🔐 Sécurité

### Protection contre les injections

#### SQL Injection
- **Détection de patterns** : `UNION`, `SELECT`, `DROP`, `--`, `/*`, etc.
- **ORM SQLAlchemy** : Prepared statements automatiques
- **Validation stricte** des inputs

#### XSS (Cross-Site Scripting)
- **Échappement HTML** de tous les inputs utilisateurs
- **Détection de patterns** : `<script>`, `javascript:`, `onclick=`, `<iframe>`, etc.
- **Sanitization** avant insertion en base

### Validations implémentées

```python
# Fonctions dans app/core/security.py

validate_email(email)                    # Format email valide
validate_name(name, field_name)         # Lettres, accents, tirets, apostrophes
validate_company_name(company)          # + chiffres et &().
validate_password_strength(password)    # Min 8 car, maj, min, chiffre
validate_integer(value, min, max)       # Plage numérique
sanitize_string(value, max_length)      # Échappement HTML
detect_sql_injection(value)             # Détection SQL malveillant
detect_xss(value)                       # Détection XSS
validate_input_security(value)          # Validation globale
```

---

## 📧 Système d'emails (SMTP)

### Templates emails

#### Email de vérification
- Design moderne avec gradient
- Bouton call-to-action
- Lien de secours
- Expire après 24h

#### Email d'approbation de compte
- Message de bienvenue
- Bouton "Se connecter"
- Liste des fonctionnalités disponibles

### Configuration SMTP (.env)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=mot-de-passe-application
SMTP_FROM_EMAIL=noreply@mibsai.com
SMTP_FROM_NAME=MIBS AI
```

---

## 🎨 Interface Frontend

### Pages créées

1. **Home (`/`)**
   - Hero section
   - Feature cards
   - Modals Login/Register
   - Header avec navigation contextuelle

2. **Admin Panel (`/admin`)**
   - Accessible : Admin + Modérateur
   - Statistiques (total, actifs, en attente, modérateurs)
   - Gestion des utilisateurs avec tableau
   - Menu déroulant d'actions par utilisateur
   - Barre de recherche (filtrage temps réel)

3. **Admin Dev (`/admin/dev`)**
   - Accessible : Admin uniquement
   - Tests backend/database
   - Formulaires d'inscription/connexion de test
   - Affichage des infos utilisateur

4. **Verify Email (`/verify-email`)**
   - Validation automatique du token
   - Feedback visuel (success/error)
   - Redirection automatique

### Composants réutilisables

- **Header** : Navigation commune à toutes les pages
- **LoginModal** : Connexion avec gestion d'erreurs
- **RegisterModal** : Inscription avec validation frontend
- **Modal** : Composant générique pour pop-ups
- **UserTable** : Tableau de gestion des utilisateurs
- **StatsCards** : Cartes de statistiques
- **ModeratorModal** : Nomination de modérateur

### Styles

- **Thème** : Dark/Light automatique selon système
- **Variables CSS** : Couleurs, espacements cohérents
- **Responsive** : Mobile-friendly
- **Animations** : Transitions fluides

---

## 🔧 Configuration et déploiement

### Variables d'environnement (.env)

```env
# ========== DATABASE ==========
POSTGRES_USER=juridique_user
POSTGRES_PASSWORD=***
POSTGRES_DB=juridique_ai
POSTGRES_PORT=5432
POSTGRES_HOST=database

# ========== BACKEND API ==========
HOST=0.0.0.0
PORT=8000
WORKERS=1
ENVIRONMENT=development

# ========== FRONTEND ==========
FRONTEND_URL=http://localhost:5173

# ========== SMTP ==========
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=***
SMTP_PASSWORD=***
SMTP_FROM_EMAIL=noreply@mibsai.com
SMTP_FROM_NAME=MIBS AI

# ========== JWT ==========
SECRET_KEY=*** (généré automatiquement)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# ========== ADMIN ACCOUNT ==========
ADMIN_EMAIL=admin@mibsai.com
ADMIN_PASSWORD=***
ADMIN_PRENOM=Admin
ADMIN_NOM=System
ADMIN_ENTREPRISE=MIBS AI
```

### Création automatique du compte admin

Au démarrage du backend, si les variables `ADMIN_EMAIL` et `ADMIN_PASSWORD` sont définies :
- Création automatique du compte admin
- `is_admin=True`, `is_active=True`, `email_verified=True`
- Mise à jour si le compte existe déjà

---

## 📁 Structure des fichiers

### Backend
```
backend/
├── app/
│   ├── auth/
│   │   ├── router.py           # Routes d'authentification
│   │   ├── admin_router.py     # Routes admin/modérateur
│   │   ├── service.py          # Logique métier + validations
│   │   ├── schemas.py          # Schémas Pydantic
│   │   └── dependencies.py     # Dépendances JWT
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   ├── security.py         # JWT + Validations
│   │   └── email.py            # SMTP + Templates
│   ├── database/
│   │   ├── models.py           # Modèles SQLAlchemy
│   │   ├── base.py             # Session DB
│   │   └── init_db.py          # Init + admin auto
│   └── main.py                 # Point d'entrée FastAPI
```

### Frontend
```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── Modal.jsx
│   │   │   ├── LoginModal.jsx
│   │   │   └── RegisterModal.jsx
│   │   ├── admin/
│   │   │   ├── UserTable.jsx
│   │   │   ├── StatsCards.jsx
│   │   │   ├── UserManagement.jsx
│   │   │   └── ModeratorModal.jsx
│   │   ├── dev/
│   │   │   ├── BackendStatus.jsx
│   │   │   ├── DatabaseStatus.jsx
│   │   │   └── AuthSection.jsx
│   │   └── layout/
│   │       └── Header.jsx
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── AdminPanel.jsx
│   │   ├── AdminDev.jsx
│   │   └── VerifyEmail.jsx
│   ├── styles/
│   │   ├── App.css
│   │   ├── Home.css
│   │   ├── AdminPanel.css
│   │   ├── AdminDev.css
│   │   └── Header.css
│   ├── App.jsx
│   └── main.jsx
```

---

## 🚀 API Endpoints

### Authentification (`/api/auth`)

```
POST   /register              # Inscription
POST   /login                 # Connexion
GET    /verify-email          # Vérification email
GET    /me                    # Infos utilisateur connecté
GET    /account-status        # Statut du compte
```

### Administration (`/api/admin`)

```
GET    /users                 # Liste utilisateurs (avec filtres)
PATCH  /users/{id}            # Modifier utilisateur
DELETE /users/{id}            # Supprimer utilisateur
GET    /stats                 # Statistiques
```

### Général

```
GET    /                      # Health check
GET    /api/health            # Status détaillé
GET    /api/test-db           # Test connexion DB
```

---

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : Framework web moderne
- **SQLAlchemy** : ORM Python
- **PostgreSQL** : Base de données
- **Pydantic** : Validation de données
- **Jose** : JWT tokens
- **Passlib** : Hashing bcrypt
- **aiosmtplib** : Emails async

### Frontend
- **React 18** : UI library
- **React Router** : Navigation
- **Axios** : Requêtes HTTP
- **Vite** : Build tool

### DevOps
- **Docker** : Conteneurisation
- **Docker Compose** : Orchestration

---

## 📝 Fonctionnalités Admin Panel

### Statistiques affichées
- **Total utilisateurs**
- **Utilisateurs actifs**
- **En attente de validation**
- **Nombre de modérateurs** (admin seulement)
- **Limite utilisateurs** (modérateur)

### Actions sur les utilisateurs

**Utilisateurs en attente :**
- ✅ Accepter
- ❌ Refuser

**Utilisateurs actifs :**
- 🛡️ Nommer modérateur (admin)
- 🔄 Retirer modérateur (admin)
- ⏸ Désactiver
- 🗑️ Supprimer

**Protections :**
- ❌ Impossible de modifier les admins
- ❌ Modérateur ne peut gérer que son entreprise
- ❌ Limite `max_users` vérifiée avant activation

### Filtres et recherche
- **Onglets** : En attente / Actifs / Tous
- **Recherche** : Temps réel sur nom, prénom, email, entreprise
- **Menu déroulant** : Sélection d'action + bouton Valider

---

## 🔒 Corrections de bugs

1. **Double vérification email** (React StrictMode)
   - Fix : `useRef` pour éviter double exécution

2. **Alignement boutons** (CSS conflicts)
   - Fix : Sélecteurs spécifiques + `!important`

3. **NameError schemas.py**
   - Fix : Déplacement `TokenWithUser` après `UserResponse`

4. **Modal inputs différentes tailles**
   - Fix : `box-sizing: border-box` + `width: 100%`

---

## ✅ Tests et validation

### Tests manuels effectués

- [x] Inscription utilisateur
- [x] Envoi email de vérification
- [x] Validation email via lien
- [x] Connexion utilisateur
- [x] Token JWT persistant
- [x] Approbation compte par admin
- [x] Envoi email d'approbation
- [x] Nomination modérateur
- [x] Vérification limite utilisateurs
- [x] Retrait statut modérateur
- [x] Recherche utilisateurs
- [x] Protection admins
- [x] Redirection selon rôles
- [x] Header unifié toutes pages
- [x] Validation inputs (XSS/SQL)
- [x] Échappement HTML

---

## 📌 Points importants

### Sécurité
- ✅ Mots de passe hashés avec bcrypt
- ✅ JWT avec expiration (30 jours)
- ✅ Protection CORS configurée
- ✅ Validation stricte tous inputs
- ✅ Détection XSS et SQL injection
- ✅ Échappement HTML systématique
- ✅ Tokens de vérification uniques
- ✅ Protection routes backend/frontend

### UX/UI
- ✅ Messages d'erreur clairs
- ✅ Confirmations avant suppressions
- ✅ Feedback visuel (loading, success, error)
- ✅ Responsive design
- ✅ Thème dark/light auto
- ✅ Navigation intuitive

### Code Quality
- ✅ Commentaires en français
- ✅ Docstrings complètes
- ✅ Séparation concerns (MVC)
- ✅ Composants réutilisables
- ✅ Variables d'environnement
- ✅ Gestion d'erreurs complète

---

## 🎯 Prochaines étapes suggérées

1. **Dashboard utilisateur** : Page pour utilisateurs connectés
2. **Système de chat IA** : Utiliser le modèle Chat existant
3. **Recherche juridique** : Intégration Légifrance
4. **Débat contradictoire** : IA arguments pour/contre
5. **Logs d'activité** : Audit trail des actions admin
6. **Reset password** : Mot de passe oublié
7. **2FA** : Authentification double facteur
8. **Rate limiting** : Protection contre brute force

---

## 📞 Support et documentation

### Documentation utilisée
- FastAPI : https://fastapi.tiangolo.com/
- React : https://react.dev/
- SQLAlchemy : https://www.sqlalchemy.org/

### Commandes utiles

```bash
# Backend
cd backend
docker-compose up

# Frontend
cd frontend
npm install
npm run dev

# Database reset
docker-compose down -v
docker-compose up
```

---

**Version** : 1.0.0
**Date** : 30 Novembre 2024
**Auteurs** : Équipe MIBS AI
**Statut** : ✅ Prêt pour production (avec configuration SMTP)
