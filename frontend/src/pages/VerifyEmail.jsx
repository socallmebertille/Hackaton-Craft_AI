import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import axios from 'axios'
import '../styles/VerifyEmail.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('loading') // loading, success, error
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const hasVerified = useRef(false)

  useEffect(() => {
    const verifyEmail = async () => {
      // Empêcher les doubles exécutions (React StrictMode)
      if (hasVerified.current) {
        return
      }
      hasVerified.current = true

      const token = searchParams.get('token')

      if (!token) {
        setStatus('error')
        setMessage('Token de vérification manquant')
        return
      }

      try {
        const response = await axios.get(`${API_URL}/api/auth/verify-email`, {
          params: { token }
        })

        setStatus('success')
        setEmail(response.data.email)
        setMessage('Votre email a été vérifié avec succès !')

        // Redirection automatique après 3 secondes
        setTimeout(() => {
          navigate('/admin/dev')
        }, 3000)
      } catch (err) {
        const errorDetail = err.response?.data?.detail || 'Une erreur est survenue lors de la vérification'

        // Si l'email est déjà vérifié, c'est techniquement un succès
        if (errorDetail === 'Email déjà vérifié') {
          setStatus('success')
          setMessage('Votre email est déjà vérifié !')
          setTimeout(() => {
            navigate('/admin/dev')
          }, 3000)
        } else {
          setStatus('error')
          setMessage(errorDetail)
        }
      }
    }

    verifyEmail()
  }, [searchParams, navigate])

  return (
    <div className="verify-email">
      <div className="verify-card">
        {status === 'loading' && (
          <>
            <div className="spinner"></div>
            <h1>Vérification en cours...</h1>
            <p>Veuillez patienter pendant que nous vérifions votre email</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="success-icon">✓</div>
            <h1>Email vérifié !</h1>
            <p className="email">{email}</p>
            <p className="message">{message}</p>
            <p className="info">Votre compte est maintenant en attente de validation par un administrateur.</p>
            <p className="redirect">Redirection automatique vers la page de connexion...</p>
            <Link to="/admin/dev" className="btn-primary">Aller à la page de connexion</Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="error-icon">✗</div>
            <h1>Erreur de vérification</h1>
            <p className="error-message">{message}</p>
            <p className="info">Le lien de vérification est peut-être expiré ou invalide.</p>
            <Link to="/admin/dev" className="btn-primary">Retour à la page de connexion</Link>
          </>
        )}
      </div>
    </div>
  )
}

export default VerifyEmail
