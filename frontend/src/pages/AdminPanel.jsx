import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import Header from '../components/layout/Header'
import UserManagement from '../components/admin/UserManagement'
import StatsCards from '../components/admin/StatsCards'
import '../styles/admin/index.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function AdminPanel() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  // Vérifier si l'utilisateur est connecté et admin/modérateur
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('jwt_token')
      if (!token) {
        navigate('/')
        return
      }

      try {
        const response = await axios.get(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })

        // Vérifier si l'utilisateur est admin ou modérateur
        if (!response.data.is_admin && !response.data.is_moderator) {
          navigate('/')
          return
        }

        setUser(response.data)

        // Charger les statistiques
        const statsResponse = await axios.get(`${API_URL}/api/admin/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setStats(statsResponse.data)

        setLoading(false)
      } catch (err) {
        localStorage.removeItem('jwt_token')
        navigate('/')
      }
    }

    checkAuth()
  }, [navigate])

  const handleLogout = () => {
    localStorage.removeItem('jwt_token')
    navigate('/')
  }

  const refreshStats = async () => {
    try {
      const token = localStorage.getItem('jwt_token')
      const statsResponse = await axios.get(`${API_URL}/api/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setStats(statsResponse.data)
    } catch (err) {
      console.error('Erreur lors du refresh des stats:', err)
    }
  }

  // Afficher un loader pendant la vérification
  if (loading) {
    return (
      <div className="admin-panel">
        <Header user={null} />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Vérification des permissions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-panel">
      {/* Header */}
      <Header user={user} onLogout={handleLogout} />

      <div className="admin-content">
        <div className="admin-title">
          <h2>{user?.is_admin ? 'Panneau d\'administration' : 'Gestion des utilisateurs'}</h2>
          {user?.is_moderator && !user?.is_admin && (
            <p className="company-info">Entreprise : {user.moderator_company}</p>
          )}
        </div>

        {/* Statistiques */}
        {stats && <StatsCards stats={stats} user={user} />}

        {/* Gestion des utilisateurs */}
        <UserManagement user={user} onUpdate={refreshStats} />
      </div>
    </div>
  )
}

export default AdminPanel
