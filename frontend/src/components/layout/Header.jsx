import { Link, useNavigate } from 'react-router-dom'
import '../../styles/Header.css'

function Header({ user, onLogout, onShowLogin, onShowRegister }) {
  const navigate = useNavigate()

  const handleLogout = () => {
    if (onLogout) {
      onLogout()
    } else {
      localStorage.removeItem('jwt_token')
      navigate('/')
    }
  }

  return (
    <header className="app-header">
      <div className="header-content">
        <Link to="/" className="logo">
          <img src="/assets/images/white_logo_MIBS.png" alt="MIBS Logo" className="logo-img" />
          <h1>MIBS AI</h1>
        </Link>
        <nav className="nav-links">
          {(user?.is_admin || user?.is_moderator) && (
            <Link to="/admin" className="nav-link">Admin Panel</Link>
          )}
          {user?.is_admin && (
            <Link to="/admin/dev" className="nav-link">Dev Panel</Link>
          )}
          {user ? (
            <div className="user-menu">
              <span className="user-name">{user.prenom} {user.nom}</span>
              <button onClick={handleLogout} className="btn-secondary">Déconnexion</button>
            </div>
          ) : (
            onShowLogin && onShowRegister && (
              <div className="auth-buttons">
                <button onClick={onShowLogin} className="btn-secondary">
                  Connexion
                </button>
                <button onClick={onShowRegister} className="btn-primary">
                  Inscription
                </button>
              </div>
            )
          )}
        </nav>
      </div>
    </header>
  )
}

export default Header
