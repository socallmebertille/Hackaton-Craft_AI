<div align="center">
  <h1>Juridique AI</h1>
  
  <p><strong>Assistant Juridique Intelligent - Hackathon 42 Paris x CraftAI</strong></p>
  
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-latest-009688?style=flat&logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-enabled-2496ED?style=flat&logo=docker&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white">

  <p><em>Assistant juridique de génération de débats juridiques contradictoires via IA pour l'analyse de questions juridiques françaises</em></p>
</div>

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
  - [Problématique](#problématique)
  - [Solution](#solution)
- [Stack technique](#-stack-technique)
- [Structure du projet - Clean Architecture par Features](#-structure-du-projet---clean-architecture-par-features)
- [Pipelines IA - Approche théorique](#-pipelines-ia---approche-théorique)
  - [Pipeline 0: Analyse d'intention](#pipeline-0-analyse-dintention)
  - [Pipeline 1: Extraction de concepts](#pipeline-1-extraction-de-concepts)
  - [Pipeline 3: Débat contradictoire](#pipeline-3-débat-contradictoire)
  - [Pipeline 4: Citations juridiques](#pipeline-4-citations-juridiques)
- [Installation](#-installation)
- [Déploiement des pipelines](#-déploiement-des-pipelines)
- [API Endpoints](#-api-endpoints)
- [Documentation](#-documentation)

---

## Vue d'ensemble

**Juridique AI** est un assistant juridique intelligent développé dans le cadre d'un hackathon organisé par **42 Paris** en collaboration avec **CraftAI**. L'objectif est de fournir une analyse juridique approfondie des questions relatives au droit français en générant des **débats contradictoires structurés**.

### Problématique

Comment permettre à un utilisateur de comprendre tous les aspects d'une question juridique complexe, en présentant les arguments **pour** et **contre**, tout en s'appuyant sur des **sources légales vérifiées** ?

### Solution

Un système de pipelines IA modulaires qui :
1. **Analyse l'intention** de l'utilisateur (débat, citations, hors-sujet)
2. **Extrait les concepts juridiques** pertinents
3. **Récupère les données légales** via l'API Légifrance
4. **Génère un débat structuré** avec arguments contradictoires
5. **Fournit des citations** avec explications contextuelles

---

## Stack Technique

| Composant              | Technologie             | Rôle                                           |
|------------------------|-------------------------|------------------------------------------------|
| **Backend**            | FastAPI (Python 3.11)   | API REST, orchestration des pipelines          |
| **Frontend**           | React 18 + Vite         | Interface utilisateur moderne                  |
| **Base de données**    | PostgreSQL 15           | Stockage des conversations et métadonnées      |
| **IA - LLM**           | Mistral AI              | Analyse sémantique, génération de texte        |
| **IA - Orchestration** | CraftAI Pipelines       | Déploiement et gestion des workflows IA        |
| **Source légale**      | API Légifrance          | Accès aux textes juridiques français officiels |
| **Containerisation**   | Docker + Docker Compose | Environnement de développement/production      |
| **Reverse Proxy**      | Nginx                   | Routage frontend/backend                       |

---

## Structure du Projet - Clean Architecture par Features

```
Juridique-AI/
├── backend/                 # API FastAPI
|   ├── app/                 # Code source de l'API
│   │   ├── admin/           # Endpoints d'administration
│   │   ├── ai/              # Pipelines IA et intégrations
│   │   │   ├── pipelines/   # Code des pipelines CraftAI
│   │   │   ├── services/    # Services métier (mistral_service.py, etc.)
│   │   │   ├── scripts/     # Scripts upload/deploy des pipelines
│   │   │   └── requirements.txt
│   │   ├── auth/            # Authentification et gestion des utilisateurs
│   │   ├── chat/            # Logique métier des conversations et orchestration des réponses IA
│   │   ├── core/            # Configuration globale, dépendances, middlewares
│   │   ├── database/        # Gestion de la base de données
│   │   └── main.py          # Création de l'app FastAPI et déclaration des routes
│   ├── examples/            # Exemples CraftAI et Légifrance
│   ├── requirements.txt     # Dépendances Python
│   └── Dockerfile           # Image Docker du backend
├── frontend/                # Application Frontend web
|   ├── assets/              # Assets globaux (images, icônes, fonts)
|   ├── legal/               # Contenu juridique statique ou expérimental (RGPD, CGU, etc.)
|   ├── public/              # Fichiers publics
│   ├── src/                 # Code source React
│   │   ├── components/      # Composants UI réutilisables
│   │   ├── config/          # Configuration (API URLs, constantes, settings)
│   │   ├── pages/           # Pages principales de l'application
│   │   ├── styles/          # Styles globaux (CSS)
|   │   ├── App.jsx          # Composant racine React
│   │   └── main.jsx         # Point d'entrée React (bootstrap de l'app)
|   ├── index.html           # Template HTML principal
│   └── Dockerfile           # Image Docker du frontend
└── docker-compose.yml       # Orchestration Docker (frontend + backend + services)
```

---

## Pipelines IA - Approche théorique

Les pipelines sont hébergés sur **CraftAI** et appelés via des endpoints REST. Chaque pipeline est un conteneur Docker isolé contenant le code Python, les dépendances et les services métier nécessaires.

### Pipeline 0: Analyse d'intention

**Objectif** : Classifier l'intention de l'utilisateur avant de router vers le bon pipeline.

**Théorie** : Avant de traiter une question juridique, il faut comprendre **ce que l'utilisateur attend réellement**. S'agit-il d'une question complexe nécessitant une analyse approfondie ? D'une simple demande de références légales ? Ou d'une question hors-sujet ?

**Process** :
1. Envoi du message à Mistral AI avec un prompt de classification
2. Le modèle retourne une intention parmi :
   - DEBAT : Question complexe nécessitant une analyse approfondie
   - CITATIONS : Demande de références légales précises
   - HORS_SUJET : Question non juridique

### Pipeline 1: Extraction de concepts

**Objectif** : Identifier les concepts juridiques clés pour interroger l'API Légifrance de manière efficace.

**Théorie** : L'API Légifrance nécessite des paramètres de recherche précis (codes juridiques, concepts, nature des textes). Ce pipeline utilise la compréhension sémantique de Mistral AI pour extraire automatiquement ces informations d'une question en langage naturel.

**Process** :
1. Mistral AI analyse la question et extrait :
   - Codes juridiques concernés (ex: Code civil → LEGITEXT000006070721)
   - Concepts juridiques (ex: "contrat", "consentement", "capacité")
   - Nature des textes recherchés (LOI, JURISPRUDENCE, ORDONNANCE, etc.)
2. Formattage pour requête Légifrance

### Pipeline 3: Débat contradictoire

**Objectif** : Générer un débat structuré avec arguments pour et contre en s'appuyant sur les textes légaux.

**Théorie** : Cette approche s'inspire des débats adversariaux en droit, où chaque partie présente ses arguments avant qu'une décision équilibrée ne soit prise. Le pipeline implémente un algorithme de débat en 4 rounds :
1. Round 1 - Pour : Génération de 3 arguments favorables basés sur les textes légaux
2. Round 1 - Contre : Génération de 3 contre-arguments réfutant les arguments précédents
3. Round 2 - Pour : Réfutation des contre-arguments du round 1
4. Round 2 - Contre : Réfutation finale et consolidation
5. Synthèse : Analyse équilibrée avec recommandation juridique

**Process** (algorithme en 4 rounds) :
Round 1:
  POUR   → 3 arguments pro-licenciement (basés sur exceptions légales)
  CONTRE → 3 arguments anti-licenciement (protection légale, jurisprudence)

Round 2:
  POUR   → Réfutation des contre-arguments (cas d'autorisation)
  CONTRE → Réfutation finale (conditions strictes)

Synthèse:
  → Analyse équilibrée des deux positions
  → Recommandation juridique nuancée

### Pipeline 4: Citations juridiques

**Objectif** : Fournir des références légales précises avec explications contextuelles accessibles.

**Théorie** : Les textes juridiques sont souvent complexes et nécessitent une expertise pour être compris. Ce pipeline sélectionne les articles/décisions pertinents et génère des explications vulgarisées pour rendre le droit accessible.

**Process** :
1. Sélection des 3-5 références les plus pertinentes via scoring sémantique
2. Génération d'explications en langage clair pour chaque référence
3. Structuration en format citation avec source vérifiable

---

## Installation et Lancement

### Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- Git

### Lancement avec Docker (Recommandé)

1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd Juridique-AI
   ```

2. **Créer le fichier .env**
   ```bash
   cp .env.example .env
   ```
Éditer .env avec vos clés API :
   ```bash
   # Mistral AI
   MISTRAL_API_KEY=votre_clé_mistral

   # CraftAI
   CRAFT_AI_SDK_TOKEN=votre_token_craftai
   CRAFT_AI_ENVIRONMENT_URL=votre_url_environment

   # Légifrance (optionnel)
   MIBS_LEGIFRANCE_CLIENT_ID=votre_client_id
   MIBS_LEGIFRANCE_CLIENT_SECRET=votre_secret
   ```

3. **Lancer les services**
   ```bash
   # Production
   docker-compose up -d --build
   ```

4. **Accéder à l'application**
   - Frontend : http://localhost:5173 (dev) ou http://localhost (prod)
   - Backend API : http://localhost:8000
   - Documentation API : http://localhost:8000/docs

### Lancement en local (Sans Docker)

#### Backend

```bash
cd backend
python -m app.main
# OU
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Déploiement des Pipelines

Les pipelines CraftAI nécessitent deux étapes.

Étape 1 : Upload d'un pipeline
Exemple avec le Pipeline 0 (analyse d'intention) :
```bash
cd backend/app/ai
python scripts/upload_pipeline_0.py
```

Étape 2 : Déploiement (création d'un endpoint)
```bash
cd backend/app/ai
python scripts/deploy_pipeline_0.py
```

Important : Copier ces informations dans .env :
```
PIPELINE_0_ENDPOINT_URL=https://xxx.craftai.ai/pipelines/analyze-intent
PIPELINE_0_ENDPOINT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## API Endpoints

### Authentification

| Méthode | Endpoint                  | Description                                |
|---------|---------------------------|--------------------------------------------|
| `POST`  | `/api/auth/register`      | Inscription (email de vérification envoyé) |
| `POST`  | `/api/auth/login`         | Connexion (retourne JWT token)             |
| `GET`   | `/api/auth/verify-email`  | Vérification email via token               |
| `GET`   | `/api/auth/me`            | Informations utilisateur connecté          |

### Chat

| Méthode | Endpoint                       | Description                               |
|---------|--------------------------------|-------------------------------------------|
| `POST`  | `/api/chat/new`                | Créer une nouvelle conversation           |
| `POST`  | `/api/chat/message`            | Envoyer un message (orchestration IA)     |
| `GET`   | `/api/chat/list`               | Lister les conversations de l'utilisateur |
| `GET`   | `/api/chat/{chat_id}/messages` | Récupérer tous les messages d'un chat     |

### Administration

| Méthode  | Endpoint                | Description                                |
|----------|-------------------------|--------------------------------------------|
| `GET`    | `/api/admin/users`      | Lister les utilisateurs (admin/modérateur) |
| `PATCH`  | `/api/admin/users/{id}` | Mettre à jour un utilisateur               |
| `DELETE` | `/api/admin/users/{id}` | Supprimer un utilisateur                   |
| `GET`    | `/api/admin/stats`      | Statistiques d'utilisation                 |

### Santé

| Méthode | Endpoint      | Description                |
|---------|---------------|----------------------------|
| `GET`   | `/`           | Health check basique       |
| `GET`   | `/api/health` | Statut détaillé du backend |
| `GET`   | `/docs`       | Documentation Swagger UI   |

---

## Documentation

- **Pipelines IA** : `backend/app/ai/README.md`
- **Exemples CraftAI** : `backend/examples/craftai/`
- **Exemples Légifrance** : `backend/examples/legifrance/`

## License

Ce projet a été développé dans le cadre du hackathon 42 Paris x CraftAI.

Propriétaire - MIBS
