import { useState, useEffect } from 'react'
import axios from 'axios'
import RegisterForm from './RegisterForm'
import LoginForm from './LoginForm'
import UserInfo from './UserInfo'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function AuthSection() {
  const [authResponse, setAuthResponse] = useState(null)
  const [authError, setAuthError] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('jwt_token') || null)
  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    const fetchCurrentUser = async () => {
      if (!token) return
      try {
        const response = await axios.get(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setCurrentUser(response.data)
      } catch (err) {
        console.error('Token invalide:', err)
        setToken(null)
        localStorage.removeItem('jwt_token')
      }
    }
    fetchCurrentUser()
  }, [token])

  const handleRegister = async (formData) => {
    setAuthError(null)
    setAuthResponse(null)
    try {
      const response = await axios.post(`${API_URL}/api/auth/register`, formData)
      setAuthResponse({ type: 'register', data: response.data })
    } catch (err) {
      setAuthError(err.response?.data?.detail || err.message)
    }
  }

  const handleLogin = async (formData) => {
    setAuthError(null)
    setAuthResponse(null)
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, formData)
      const accessToken = response.data.access_token
      setToken(accessToken)
      localStorage.setItem('jwt_token', accessToken)
      setAuthResponse({ type: 'login', data: response.data })
    } catch (err) {
      setAuthError(err.response?.data?.detail || err.message)
    }
  }

  const handleLogout = () => {
    setToken(null)
    setCurrentUser(null)
    localStorage.removeItem('jwt_token')
    setAuthResponse(null)
  }

  const handleDeleteAccount = async () => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.')) return
    try {
      await axios.delete(`${API_URL}/api/auth/account`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setAuthResponse({ type: 'delete', message: 'Compte supprimé avec succès' })
      handleLogout()
    } catch (err) {
      setAuthError(err.response?.data?.detail || err.message)
    }
  }

  return (
    <div className="auth-section">
      <h2>Test d'Authentification</h2>

      {authError && <div className="error-message">{authError}</div>}
      {authResponse && (
        <div className="success-message">
          {authResponse.type === 'register' && (
            <p>✓ Inscription réussie ! Email: {authResponse.data.email}<br/>
            <small>Vérifiez votre email pour activer votre compte</small></p>
          )}
          {authResponse.type === 'login' && (
            <p>✓ Connexion réussie ! Token enregistré</p>
          )}
          {authResponse.type === 'delete' && (
            <p>✓ {authResponse.message}</p>
          )}
        </div>
      )}

      {currentUser ? (
        <UserInfo
          user={currentUser}
          onLogout={handleLogout}
          onDeleteAccount={handleDeleteAccount}
        />
      ) : (
        <div className="auth-forms">
          <RegisterForm onRegister={handleRegister} />
          <LoginForm onLogin={handleLogin} />
        </div>
      )}
    </div>
  )
}

export default AuthSection
