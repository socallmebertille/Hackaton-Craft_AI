# Pipeline CraftAI - Analyse d'Intention

Ce dossier contient le pipeline CraftAI pour l'analyse d'intention des messages utilisateurs dans l'application Juridique AI.

## 📋 Vue d'ensemble

Le pipeline `analyze_intent` utilise Mistral AI pour déterminer l'intention de l'utilisateur :

- **DEBAT** : L'utilisateur souhaite une discussion approfondie, une explication ou une analyse juridique
- **CITATIONS** : L'utilisateur cherche des références légales précises (articles de loi, jurisprudence)
- **HORS_SUJET** : Le message n'est pas lié au domaine juridique

## 🗂️ Structure du projet

```
backend/app/ai/
├── pipelines/
│   └── analyze_intent.py         # Pipeline CraftAI principal
├── services/
│   └── mistral_service.py        # Service Mistral AI
├── scripts/
│   ├── upload_pipeline_0.py      # Script d'upload Pipeline 0 vers CraftAI
│   └── deploy_pipeline_0.py      # Script de déploiement Pipeline 0
├── requirements.txt              # Dépendances pour CraftAI
└── README.md                     # Cette documentation
```

## 🚀 Installation et Configuration

### 1. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

Créez un fichier `.env` à partir de `.env.example` et configurez :

```env
# Mistral AI
MISTRAL_API_KEY=votre_clé_mistral
MISTRAL_MODEL_SMALL=mistral-small-latest

# CraftAI
CRAFT_AI_SDK_TOKEN=votre_token_craftai
CRAFT_AI_ENVIRONMENT_URL=votre_url_environment

# Pipeline 0 - Analyze Intent (rempli après déploiement)
PIPELINE_0_ENDPOINT_URL=votre_endpoint_url
PIPELINE_0_ENDPOINT_TOKEN=votre_endpoint_token
```

## 🧪 Tests locaux

### Tester le service Mistral

```bash
cd backend/app/ai
python services/mistral_service.py
```

### Tester le pipeline

```bash
cd backend/app/ai
python pipelines/analyze_intent.py
```

## 📤 Upload et Déploiement sur CraftAI

### 1. Upload du pipeline

```bash
cd backend/app/ai
python scripts/upload_pipeline_0.py
```

Ce script va :
- Vérifier les variables d'environnement
- Supprimer l'ancien pipeline s'il existe
- Créer un nouveau pipeline sur CraftAI avec :
  - Input : `message` (string)
  - Output : `result` (json avec intention, confidence, reasoning)

### 2. Déploiement

```bash
cd backend/app/ai
python scripts/deploy_pipeline_0.py
```

Ce script va :
- Créer un deployment avec execution_rule ENDPOINT
- Fournir l'URL de l'endpoint et le token d'authentification
- **Important** : Copiez ces informations dans votre `.env` :
  - `PIPELINE_0_ENDPOINT_URL`
  - `PIPELINE_0_ENDPOINT_TOKEN`

## 📊 Format des données

### Input

```json
{
  "message": "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?"
}
```

### Output

```json
{
  "result": {
    "message": "Quelles sont les conséquences juridiques de la dissolution d'un PACS ?",
    "intention": "DEBAT",
    "confidence": 0.95,
    "reasoning": "L'utilisateur demande une explication approfondie sur les conséquences juridiques, ce qui indique une intention de débat/discussion"
  }
}
```

## 🔧 Utilisation de l'API

Une fois déployé, vous pouvez appeler le pipeline via l'endpoint :

```bash
curl -X POST https://your-craftai-endpoint/execute \
  -H "Authorization: EndpointToken YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cite-moi les articles du Code civil sur le PACS"
  }'
```

## 🎯 Types d'intentions

### DEBAT
- Questions ouvertes nécessitant des explications
- Demandes d'analyse juridique
- Questions "Comment...", "Pourquoi...", "Quelles sont..."
- Exemples :
  - "Comment fonctionne la dissolution d'un PACS ?"
  - "Quelles sont les conséquences d'un licenciement abusif ?"

### CITATIONS
- Demandes de références légales précises
- Recherche d'articles de loi ou de jurisprudence
- Mots-clés : "cite", "article", "texte de loi", "jurisprudence"
- Exemples :
  - "Cite-moi les articles du Code civil sur le mariage"
  - "Quelle jurisprudence existe sur le droit au logement ?"

### HORS_SUJET
- Messages non liés au domaine juridique
- Questions personnelles
- Spam ou messages inappropriés
- Exemples :
  - "Quel temps fait-il ?"
  - "Raconte-moi une blague"

## 🛠️ Maintenance

### Mettre à jour le pipeline

1. Modifiez le code dans `pipelines/analyze_intent.py` ou `services/mistral_service.py`
2. Testez localement
3. Re-uploadez avec `python scripts/upload_pipeline_0.py`
4. Re-déployez avec `python scripts/deploy_pipeline_0.py`
5. Mettez à jour les variables dans `.env` si nécessaire

### Surveiller les logs

Les logs sont affichés dans la console lors de l'exécution :
- `[MistralService]` : Logs du service Mistral
- `[Pipeline]` : Logs du pipeline CraftAI

## 📝 Notes importantes

- Le pipeline utilise `temperature=0.1` pour assurer la cohérence des réponses
- En cas d'erreur Mistral, le système retourne par défaut `DEBAT` avec une confidence de 0.5
- Les clés API doivent être définies dans les variables d'environnement
- Le container CraftAI utilise Python 3.12-slim

## 🔗 Liens utiles

- [Documentation CraftAI SDK](https://docs.craft.ai)
- [Documentation Mistral AI](https://docs.mistral.ai)
- [API Mistral](https://console.mistral.ai)
