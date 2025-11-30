import { useState } from 'react'
import axios from 'axios'
import Modal from './Modal'
import '../../styles/AuthModal.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function LoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, formData)
      const { access_token, user } = response.data

      // Stocker le token
      localStorage.setItem('jwt_token', access_token)

      // Appeler le callback de succès
      onLoginSuccess(user, access_token)

      // Réinitialiser le formulaire et fermer
      setFormData({ email: '', password: '' })
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue lors de la connexion')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({ email: '', password: '' })
    setError(null)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Connexion">
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
            autoFocus
          />
        </div>

        <div className="form-group">
          <label htmlFor="login-password">Mot de passe</label>
          <input
            id="login-password"
            type="password"
            placeholder="Mot de passe"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />
        </div>

        <button
          type="submit"
          className="btn-primary btn-full"
          disabled={loading}
        >
          {loading ? 'Connexion...' : 'Se connecter'}
        </button>

        <div className="form-footer">
          <a href="#" className="link-secondary">Mot de passe oublié ?</a>
        </div>
      </form>
    </Modal>
  )
}

export default LoginModal
