# Composants de développement

Ce dossier contient les composants utilisés dans la page de dev/test (`AdminDev.jsx`).

## Structure

### Composants de monitoring

- **BackendStatus.jsx** - Affiche le statut de connexion au backend FastAPI
  - Vérifie l'endpoint `/api/health`
  - Affiche la version, l'environnement et le statut

- **DatabaseStatus.jsx** - Affiche le statut de la base de données PostgreSQL
  - Vérifie l'endpoint `/api/test-db`
  - Affiche le nombre d'utilisateurs et de chats

### Composants d'authentification

- **AuthSection.jsx** - Composant principal qui gère toute la logique d'authentification
  - Gestion du token JWT dans localStorage
  - Récupération de l'utilisateur connecté
  - Handlers pour register, login, logout, delete

- **RegisterForm.jsx** - Formulaire d'inscription
  - Prénom, nom, entreprise, email, password
  - Validation de formulaire

- **LoginForm.jsx** - Formulaire de connexion
  - Email et password
  - Validation de formulaire

- **UserInfo.jsx** - Affichage des informations utilisateur connecté
  - Affiche toutes les infos de l'utilisateur
  - Boutons de déconnexion et suppression de compte

## Utilisation

Ces composants sont importés et utilisés dans `/pages/AdminDev.jsx` :

```jsx
import BackendStatus from '../components/dev/BackendStatus'
import DatabaseStatus from '../components/dev/DatabaseStatus'
import AuthSection from '../components/dev/AuthSection'

function AdminDev() {
  return (
    <div className="admin-dev">
      <div className="stats-grid">
        <BackendStatus />
        <DatabaseStatus />
      </div>
      <AuthSection />
    </div>
  )
}
```

## Avantages de cette structure

1. **Lisibilité** - Chaque composant a une responsabilité unique
2. **Maintenabilité** - Facile de modifier un composant sans affecter les autres
3. **Réutilisabilité** - Les composants peuvent être réutilisés ailleurs si nécessaire
4. **Testabilité** - Chaque composant peut être testé individuellement
