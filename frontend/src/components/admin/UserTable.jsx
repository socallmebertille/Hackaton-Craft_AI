import { useState } from 'react'
import '../../styles/admin/index.css'

function UserTable({ users, currentUser, filter, onAccept, onReject, onDeactivate, onDelete, onMakeModerator, onRemoveModerator }) {
  const [selectedActions, setSelectedActions] = useState({})

  if (users.length === 0) {
    return (
      <div className="empty-state">
        <p>Aucun utilisateur {filter === 'pending' ? 'en attente' : filter === 'active' ? 'actif' : 'trouvé'}</p>
      </div>
    )
  }

  const handleActionChange = (userId, action) => {
    setSelectedActions({ ...selectedActions, [userId]: action })
  }

  const handleActionSubmit = (userId) => {
    const action = selectedActions[userId]
    if (!action) return

    switch (action) {
      case 'accept':
        onAccept(userId)
        break
      case 'reject':
        onReject(userId)
        break
      case 'deactivate':
        onDeactivate(userId)
        break
      case 'delete':
        onDelete(userId)
        break
      case 'moderator':
        const user = users.find(u => u.id === userId)
        onMakeModerator(user)
        break
      case 'remove_moderator':
        onRemoveModerator(userId)
        break
      default:
        break
    }

    // Réinitialiser la sélection après action
    setSelectedActions({ ...selectedActions, [userId]: '' })
  }

  const getAvailableActions = (user) => {
    const actions = []

    // Aucune action sur les comptes admin
    if (user.is_admin) {
      return actions
    }

    // Actions pour utilisateurs en attente
    if (!user.is_active && user.email_verified) {
      actions.push({ value: 'accept', label: 'Accepter' })
      actions.push({ value: 'reject', label: 'Refuser' })
    }

    // Actions pour utilisateurs actifs (non admin)
    if (user.is_active && user.id !== currentUser?.id) {
      if (currentUser?.is_admin) {
        if (user.is_moderator) {
          actions.push({ value: 'remove_moderator', label: 'Retirer modérateur' })
        } else {
          actions.push({ value: 'moderator', label: 'Nommer modérateur' })
        }
      }
      actions.push({ value: 'deactivate', label: 'Désactiver' })
      actions.push({ value: 'delete', label: 'Supprimer' })
    }

    return actions
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  return (
    <div className="user-table-container">
      <table className="user-table">
        <thead>
          <tr>
            <th>Nom</th>
            <th>Email</th>
            <th>Entreprise</th>
            <th>Date d'inscription</th>
            <th>Statut</th>
            {currentUser?.is_admin && <th>Rôle</th>}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>
                <div className="user-name">
                  {user.prenom} {user.nom}
                  {user.id === currentUser?.id && <span className="badge-you">Vous</span>}
                </div>
              </td>
              <td>{user.email}</td>
              <td>{user.entreprise}</td>
              <td>{formatDate(user.date_creation)}</td>
              <td>
                <span className={`status-badge ${user.is_active ? 'active' : 'pending'}`}>
                  {user.is_active ? 'Actif' : 'En attente'}
                </span>
                {!user.email_verified && (
                  <span className="status-badge warning">Email non vérifié</span>
                )}
              </td>
              {currentUser?.is_admin && (
                <td>
                  {user.is_admin && <span className="role-badge admin">Admin</span>}
                  {user.is_moderator && <span className="role-badge moderator">Modérateur</span>}
                  {!user.is_admin && !user.is_moderator && <span className="role-badge user">Utilisateur</span>}
                </td>
              )}
              <td>
                <div className="action-dropdown">
                  {getAvailableActions(user).length > 0 ? (
                    <>
                      <select
                        value={selectedActions[user.id] || ''}
                        onChange={(e) => handleActionChange(user.id, e.target.value)}
                        className="action-select"
                      >
                        <option value="">Choisir une action</option>
                        {getAvailableActions(user).map(action => (
                          <option key={action.value} value={action.value}>
                            {action.label}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleActionSubmit(user.id)}
                        className="btn-validate"
                        disabled={!selectedActions[user.id]}
                      >
                        Valider
                      </button>
                    </>
                  ) : (
                    <span className="no-actions">-</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default UserTable
