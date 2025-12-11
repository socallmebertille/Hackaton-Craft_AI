import { useState } from 'react'
import axios from 'axios'
import Modal from './Modal'
import '../../styles/AuthModal.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function RegisterModal({ isOpen, onClose, onRegisterSuccess }) {
  const [formData, setFormData] = useState({
    prenom: '',
    nom: '',
    entreprise: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Validation du mot de passe
    if (formData.password !== formData.confirmPassword) {
      setError('Les mots de passe ne correspondent pas')
      return
    }

    if (formData.password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères')
      return
    }

    setLoading(true)

    try {
      const { confirmPassword, ...registerData } = formData
      const response = await axios.post(`${API_URL}/api/auth/register`, registerData)

      // Appeler le callback de succès
      onRegisterSuccess(response.data)

      // Réinitialiser le formulaire et fermer
      setFormData({
        prenom: '',
        nom: '',
        entreprise: '',
        email: '',
        password: '',
        confirmPassword: ''
      })
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue lors de l\'inscription')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({
      prenom: '',
      nom: '',
      entreprise: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    setError(null)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Inscription">
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="register-prenom">Prénom</label>
            <input
              id="register-prenom"
              type="text"
              placeholder="Prénom"
              value={formData.prenom}
              onChange={(e) => setFormData({...formData, prenom: e.target.value})}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="register-nom">Nom</label>
            <input
              id="register-nom"
              type="text"
              placeholder="Nom"
              value={formData.nom}
              onChange={(e) => setFormData({...formData, nom: e.target.value})}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="register-entreprise">Entreprise</label>
          <input
            id="register-entreprise"
            type="text"
            placeholder="Entreprise"
            value={formData.entreprise}
            onChange={(e) => setFormData({...formData, entreprise: e.target.value})}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="register-email">Email</label>
          <input
            id="register-email"
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="register-password">Mot de passe</label>
          <input
            id="register-password"
            type="password"
            placeholder="Mot de passe"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
            minLength={8}
          />
        </div>

        <div className="form-group">
          <label htmlFor="register-confirm-password">Confirmer le mot de passe</label>
          <input
            id="register-confirm-password"
            type="password"
            placeholder="Confirmer le mot de passe"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
            required
            minLength={8}
          />
        </div>

        <button
          type="submit"
          className="btn-primary btn-full"
          disabled={loading}
        >
          {loading ? 'Inscription...' : 'S\'inscrire'}
        </button>

        <div className="form-footer">
          <small className="text-muted">
            En vous inscrivant, vous acceptez nos conditions d'utilisation
          </small>
        </div>
      </form>
    </Modal>
  )
}

export default RegisterModal
