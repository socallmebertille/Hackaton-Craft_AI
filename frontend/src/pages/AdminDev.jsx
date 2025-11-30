import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import Header from '../components/layout/Header'
import BackendStatus from '../components/dev/BackendStatus'
import DatabaseStatus from '../components/dev/DatabaseStatus'
import AuthSection from '../components/dev/AuthSection'
import '../styles/AdminDev.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function AdminDev() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Vérifier si l'utilisateur est connecté et admin
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

        // Vérifier si l'utilisateur est admin
        if (!response.data.is_admin) {
          navigate('/')
          return
        }

        setUser(response.data)
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

  // Afficher un loader pendant la vérification
  if (loading) {
    return (
      <div className="admin-dev">
        <Header user={null} />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Vérification des permissions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-dev">
      {/* Header identique à Home */}
      <Header user={user} onLogout={handleLogout} />

      <div className="admin-content">
        <div className="admin-title">
          <h2>Monitoring et diagnostics du système</h2>
        </div>

        <div className="stats-grid">
          <BackendStatus />
          <DatabaseStatus />
        </div>

        <AuthSection />
      </div>
    </div>
  )
}

export default AdminDev
