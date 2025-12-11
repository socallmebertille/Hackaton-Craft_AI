import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import Header from '../components/layout/Header'
import LoginModal from '../components/auth/LoginModal'
import RegisterModal from '../components/auth/RegisterModal'
import '../styles/Home.css'
import { API_URL } from '../config/api'

function Home() {
  const navigate = useNavigate()
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  const [user, setUser] = useState(null)
  const [showSuccessMessage, setShowSuccessMessage] = useState(false)

  // Vérifier si l'utilisateur est déjà connecté
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('jwt_token')
      if (!token) return

      try {
        const response = await axios.get(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
        // Rediriger vers le chat si l'utilisateur est connecté
        navigate('/chat')
      } catch (err) {
        // Token invalide, le supprimer
        localStorage.removeItem('jwt_token')
      }
    }

    checkAuth()
  }, [navigate])

  const handleLoginSuccess = (userData) => {
    setUser(userData)
    // Rediriger vers le chat
    navigate('/chat')
  }

  const handleRegisterSuccess = () => {
    setShowSuccessMessage(true)
    setTimeout(() => {
      setShowSuccessMessage(false)
    }, 5000)
  }

  const handleLogout = () => {
    localStorage.removeItem('jwt_token')
    setUser(null)
  }

  const handleStart = () => {
    if (user) {
      // Rediriger vers le chat si connecté
      navigate('/chat')
    } else {
      // Afficher le modal de connexion
      setShowLoginModal(true)
    }
  }

  return (
    <div className="home">
      {/* Header avec navigation */}
      <Header
        user={user}
        onLogout={handleLogout}
        onShowLogin={() => setShowLoginModal(true)}
        onShowRegister={() => setShowRegisterModal(true)}
      />

      {/* Success message pour l'inscription */}
      {showSuccessMessage && (
        <div className="success-banner">
          <p>✓ Inscription réussie ! Vérifiez votre email pour activer votre compte.</p>
        </div>
      )}

      {/* Hero section */}
      <div className="hero">
        <h2 className="hero-title">Assistant juridique basé sur l'intelligence artificielle</h2>
        <p className="hero-subtitle">
          Analysez vos questions juridiques avec l'aide de l'IA et accédez aux textes officiels français
        </p>
        <div className="cta-buttons">
          <button className="btn-primary btn-large" onClick={handleStart}>
            Commencer
          </button>
        </div>
      </div>

      {/* Features */}
      <div className="features">
        <div className="feature-card">
          <div className="feature-icon">⚖️</div>
          <h3>Analyse Juridique</h3>
          <p>Recherche automatique dans les codes et lois françaises</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">💬</div>
          <h3>Débat Contradictoire</h3>
          <p>Arguments pour et contre générés par l'IA</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">📚</div>
          <h3>Base Légifrance</h3>
          <p>Accès aux textes officiels et jurisprudence</p>
        </div>
      </div>

      {/* Modals */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      <RegisterModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onRegisterSuccess={handleRegisterSuccess}
      />
    </div>
  )
}

export default Home
