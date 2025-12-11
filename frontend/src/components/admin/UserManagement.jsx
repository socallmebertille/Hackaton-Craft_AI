import { useState, useEffect } from 'react'
import axios from 'axios'
import UserTable from './UserTable'
import ModeratorModal from './ModeratorModal'
import '../../styles/admin/index.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function UserManagement({ user, onUpdate }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('pending') // pending, active, all
  const [searchQuery, setSearchQuery] = useState('')
  const [showModeratorModal, setShowModeratorModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)

  const loadUsers = async () => {
    try {
      const token = localStorage.getItem('jwt_token')
      const response = await axios.get(`${API_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { status_filter: filter }
      })
      setUsers(response.data.users)
      setLoading(false)
    } catch (err) {
      console.error('Erreur lors du chargement des utilisateurs:', err)
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [filter])

  const handleAccept = async (userId) => {
    try {
      const token = localStorage.getItem('jwt_token')
      await axios.patch(
        `${API_URL}/api/admin/users/${userId}`,
        { is_active: true },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      await loadUsers()
      onUpdate()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erreur lors de l\'activation'
      alert(errorMsg)
    }
  }

  const handleReject = async (userId) => {
    if (!confirm('Êtes-vous sûr de vouloir refuser cet utilisateur ?')) return

    try {
      const token = localStorage.getItem('jwt_token')
      await axios.delete(`${API_URL}/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await loadUsers()
      onUpdate()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erreur lors de la suppression'
      alert(errorMsg)
    }
  }

  const handleDeactivate = async (userId) => {
    if (!confirm('Êtes-vous sûr de vouloir désactiver cet utilisateur ?')) return

    try {
      const token = localStorage.getItem('jwt_token')
      await axios.patch(
        `${API_URL}/api/admin/users/${userId}`,
        { is_active: false },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      await loadUsers()
      onUpdate()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erreur lors de la désactivation'
      alert(errorMsg)
    }
  }

  const handleDelete = async (userId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer définitivement cet utilisateur ?')) return

    try {
      const token = localStorage.getItem('jwt_token')
      await axios.delete(`${API_URL}/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await loadUsers()
      onUpdate()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erreur lors de la suppression'
      alert(errorMsg)
    }
  }

  const handleMakeModerator = (selectedUser) => {
    setSelectedUser(selectedUser)
    setShowModeratorModal(true)
  }

  const handleRemoveModerator = async (userId) => {
    if (!confirm('Êtes-vous sûr de vouloir retirer le statut de modérateur à cet utilisateur ?')) return

    try {
      const token = localStorage.getItem('jwt_token')
      await axios.patch(
        `${API_URL}/api/admin/users/${userId}`,
        {
          is_moderator: false,
          moderator_company: null,
          max_users: null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      await loadUsers()
      onUpdate()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Erreur lors du retrait du statut de modérateur'
      alert(errorMsg)
    }
  }

  const handleModeratorUpdate = async () => {
    setShowModeratorModal(false)
    setSelectedUser(null)
    await loadUsers()
    onUpdate()
  }

  // Fonction de filtrage par recherche
  const getFilteredUsers = () => {
    if (!searchQuery.trim()) {
      return users
    }

    const query = searchQuery.toLowerCase()
    return users.filter(u => {
      return (
        u.prenom?.toLowerCase().includes(query) ||
        u.nom?.toLowerCase().includes(query) ||
        u.email?.toLowerCase().includes(query) ||
        u.entreprise?.toLowerCase().includes(query)
      )
    })
  }

  const filteredUsers = getFilteredUsers()

  if (loading) {
    return (
      <div className="user-management">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Chargement des utilisateurs...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="user-management">
      <div className="management-header">
        <h3>Gestion des utilisateurs</h3>
        <div className="filter-row">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="search-clear"
                title="Effacer la recherche"
              >
                ✕
              </button>
            )}
          </div>

          <div className="filter-tabs">
            <button
              className={`filter-tab ${filter === 'pending' ? 'active' : ''}`}
              onClick={() => setFilter('pending')}
            >
              En attente
            </button>
            <button
              className={`filter-tab ${filter === 'active' ? 'active' : ''}`}
              onClick={() => setFilter('active')}
            >
              Actifs
            </button>
            <button
              className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              Tous
            </button>
          </div>
        </div>
      </div>

      <UserTable
        users={filteredUsers}
        currentUser={user}
        filter={filter}
        onAccept={handleAccept}
        onReject={handleReject}
        onDeactivate={handleDeactivate}
        onDelete={handleDelete}
        onMakeModerator={handleMakeModerator}
        onRemoveModerator={handleRemoveModerator}
      />

      {showModeratorModal && (
        <ModeratorModal
          user={selectedUser}
          onClose={() => {
            setShowModeratorModal(false)
            setSelectedUser(null)
          }}
          onUpdate={handleModeratorUpdate}
        />
      )}
    </div>
  )
}

export default UserManagement
