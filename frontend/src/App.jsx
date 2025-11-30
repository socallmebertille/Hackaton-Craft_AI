import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import AdminDev from './pages/AdminDev'
import AdminPanel from './pages/AdminPanel'
import VerifyEmail from './pages/VerifyEmail'
import './styles/App.css'

function App() {
  // Détecter automatiquement le thème système
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = (e) => {
      document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light')
    }

    // Appliquer le thème initial
    handleChange(mediaQuery)

    // Écouter les changements
    mediaQuery.addEventListener('change', handleChange)

    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return (
    <BrowserRouter>
      <div className="app">
        <main className="main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/admin" element={<AdminPanel />} />
            <Route path="/admin/dev" element={<AdminDev />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>MIBS AI v1.0.0 - En développement</p>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
