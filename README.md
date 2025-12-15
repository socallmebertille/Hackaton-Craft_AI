# Juridique AI

Assistant juridique basé sur l'intelligence artificielle pour générer des débats contradictoires sur des questions juridiques.

## Stack Technique

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React + Vite
- **IA**: Mistral AI + CraftAI Pipelines
- **Data**: API Légifrance (textes juridiques franéais)

## Structure du Projet

```
Juridique-AI/
      backend/               # API FastAPI
      examples/         # Exemples CraftAI et Légifrance
      main.py           # Point d'entrée de l'API
      requirements.txt  # Dépendances Python
      Dockerfile.dev    # Docker pour développement
      frontend/             # Application React
      src/             # Code source
      assets/          # Images et assets
      legal/           # Documents juridiques
      package.json     # Dépendances Node
      Dockerfile.dev   # Docker pour développement
      docker-compose.dev.yml
```

## Installation et Lancement

### Prérequis

- Docker
- Docker Compose

### Lancement avec Docker (Recommandé)

1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd Juridique-AI
   ```

2. **Créer le fichier .env**
   ```bash
   cp .env.example .env
   # éditer .env si nécessaire
   ```

3. **Lancer les services**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

4. **Accéder à l'application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Documentation API: http://localhost:8000/docs

### Lancement en local (Sans Docker)

#### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# ou
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Développement

### Hot-reload

Les deux services (backend et frontend) sont configurés avec le hot-reload activé :
- Modifications du code Python é rechargement automatique FastAPI
- Modifications du code React é rechargement automatique Vite

### Arréter les services

```bash
docker-compose -f docker-compose.dev.yml down
```

### Voir les logs

```bash
# Tous les services
docker-compose -f docker-compose.dev.yml logs -f

# Backend seulement
docker-compose -f docker-compose.dev.yml logs -f backend

# Frontend seulement
docker-compose -f docker-compose.dev.yml logs -f frontend
```

## API Endpoints

- `GET /` - Health check
- `GET /api/health` - Statut détaillé du backend
- `GET /api/test` - Endpoint de test
- `GET /docs` - Documentation interactive (Swagger)

## Prochaines étapes

- [ ] Implémenter l'authentification utilisateur
- [ ] Créer l'interface de chat juridique
- [ ] Intégrer les pipelines CraftAI
- [ ] Connecter l'API Légifrance
- [ ] Générer les débats contradictoires

## Variables d'Environnement

Voir `.env.example` pour la liste compléte des variables disponibles.

Variables principales :
- `ENVIRONMENT` - Environnement (development/production)
- `PORT` - Port du backend (défaut: 8000)
- `CRAFT_AI_SDK_TOKEN` - Token CraftAI (optionnel)
- `MISTRAL_API_KEY` - Clé API Mistral (optionnel)
- `MIBS_LEGIFRANCE_CLIENT_ID` - Client ID Légifrance (optionnel)

## Documentation

- [Examples CraftAI](./backend/examples/craftai/)
- [Examples Légifrance](./backend/examples/legifrance/)

## License

Propriétaire - MIBS
