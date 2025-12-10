import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { jsPDF } from 'jspdf'
import Header from '../components/layout/Header'
import sendIcon from '../../assets/images/send_icon.png'
import '../styles/Chat.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Chat() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [sendingChatId, setSendingChatId] = useState(null) // Chat ID où le message est en cours d'envoi
  const [pdfChatId, setPdfChatId] = useState(null) // Chat ID pour lequel le PDF est disponible
  const [lastExchange, setLastExchange] = useState(null) // Dernier échange question/réponse
  const [sidebarOpen, setSidebarOpen] = useState(false) // État de la sidebar sur mobile
  const messagesEndRef = useRef(null)

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Vérifier l'authentification
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
        setUser(response.data)
        await loadChats(token)
      } catch (err) {
        console.error('Auth error:', err)
        localStorage.removeItem('jwt_token')
        navigate('/')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [navigate])

  // Charger les chats
  const loadChats = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/list`, {
        headers: { Authorization: `Bearer ${token || localStorage.getItem('jwt_token')}` }
      })
      setChats(response.data.chats || [])
    } catch (err) {
      console.error('Error loading chats:', err)
    }
  }

  // Réinitialiser pour un nouveau chat
  const startNewChat = () => {
    // Réinitialiser l'interface (le chat sera créé lors du premier message)
    setCurrentChatId(null)
    setMessages([])
    setPdfChatId(null) // Réinitialiser la pop-up PDF
  }

  // Créer un nouveau chat (appelé lors de l'envoi du premier message)
  const createNewChat = async () => {
    const token = localStorage.getItem('jwt_token')
    try {
      const response = await axios.post(
        `${API_URL}/api/chat/new`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      const newChatId = response.data.chat_id
      await loadChats(token)
      return newChatId
    } catch (err) {
      console.error('Error creating chat:', err)
      return null
    }
  }

  // Charger les messages d'un chat
  const loadMessages = async (chatId) => {
    const token = localStorage.getItem('jwt_token')
    try {
      const response = await axios.get(`${API_URL}/api/chat/${chatId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const messagesData = response.data.messages || []
      setMessages(messagesData)
      setCurrentChatId(chatId)
      setSidebarOpen(false) // Fermer la sidebar sur mobile après sélection

      // Si le chat contient des messages, préparer le PDF
      if (messagesData.length > 0) {
        // Trouver le dernier message utilisateur et les réponses assistant qui suivent
        const lastUserMsgIndex = messagesData.map(m => m.role).lastIndexOf('user')
        if (lastUserMsgIndex !== -1) {
          const userMessage = messagesData[lastUserMsgIndex]
          const assistantResponses = messagesData
            .slice(lastUserMsgIndex + 1)
            .filter(m => m.role === 'assistant')
            .map(m => m.content.message || m.content.response || '')

          if (assistantResponses.length > 0) {
            setLastExchange({
              question: userMessage.content.message || '',
              responses: assistantResponses,
              timestamp: userMessage.created_at // Heure de création du message
            })

            // Afficher la pop-up PDF pour ce chat
            setPdfChatId(chatId)
          }
        }
      }
    } catch (err) {
      console.error('Error loading messages:', err)
    }
  }

  // Générer un PDF avec la question et les réponses
  const generatePDF = () => {
    if (!lastExchange) return

    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const margin = 15
    const maxWidth = pageWidth - 2 * margin
    let yPosition = 20

    // Date et heure pour le titre et le nom de fichier (utiliser l'heure du message)
    const messageDate = new Date(lastExchange.timestamp)
    const hours = String(messageDate.getHours()).padStart(2, '0')
    const minutes = String(messageDate.getMinutes()).padStart(2, '0')
    const day = String(messageDate.getDate()).padStart(2, '0')
    const month = String(messageDate.getMonth() + 1).padStart(2, '0')
    const year = messageDate.getFullYear()
    const dateTimeTitle = `${hours}:${minutes} - ${day}/${month}/${year}`
    const fileName = `MibsAI-${hours}-${minutes}-${day}-${month}-${year}.pdf`

    // Titre centré avec date et heure
    doc.setFontSize(14)
    doc.setFont(undefined, 'bold')
    const titleWidth = doc.getTextWidth(dateTimeTitle)
    doc.text(dateTimeTitle, (pageWidth - titleWidth) / 2, yPosition)
    yPosition += 12

    // Question (h1)
    doc.setFontSize(14)
    doc.setFont(undefined, 'bold')
    doc.text('Question', margin, yPosition)
    yPosition += 8

    doc.setFont(undefined, 'normal')
    doc.setFontSize(11)
    const questionLines = doc.splitTextToSize(lastExchange.question, maxWidth)
    doc.text(questionLines, margin, yPosition)
    yPosition += questionLines.length * 6 + 10

    // Réponse (h1)
    doc.setFont(undefined, 'bold')
    doc.setFontSize(14)
    doc.text('Réponse', margin, yPosition)
    yPosition += 8

    // Traiter les réponses
    lastExchange.responses.forEach((response) => {
      // Diviser par lignes pour détecter les titres
      const lines = response.split('\n')

      lines.forEach(line => {
        // Vérifier si on doit ajouter une nouvelle page
        if (yPosition > doc.internal.pageSize.getHeight() - 20) {
          doc.addPage()
          yPosition = 20
        }

        // Détecter les titres h1 (# )
        if (line.startsWith('# ')) {
          doc.setFont(undefined, 'bold')
          doc.setFontSize(13)
          const title = line.replace(/^#\s*/, '')
          doc.text(title, margin, yPosition)
          yPosition += 8
        }
        // Détecter les titres h2 (## )
        else if (line.startsWith('## ')) {
          doc.setFont(undefined, 'bold')
          doc.setFontSize(12)
          const title = line.replace(/^##\s*/, '')
          doc.text(title, margin, yPosition)
          yPosition += 7
        }
        // Détecter les lignes avec bullet (•) - références en gras
        else if (line.startsWith('• ')) {
          const content = line.substring(2) // Enlever "• "

          // Extraire la référence (tout avant " : ")
          const colonIndex = content.indexOf(' : ')
          if (colonIndex > 0) {
            const reference = content.substring(0, colonIndex)
            const explanation = content.substring(colonIndex + 3)

            // Référence en gras
            doc.setFont(undefined, 'bold')
            doc.setFontSize(11)
            const refText = '• ' + reference.replace(/\*\*/g, '') + ' :'
            doc.text(refText, margin, yPosition)
            yPosition += 6

            // Explication en normal
            doc.setFont(undefined, 'normal')
            const explLines = doc.splitTextToSize(explanation, maxWidth - 5)
            doc.text(explLines, margin + 5, yPosition)
            yPosition += explLines.length * 6 + 2
          } else {
            // Pas de format spécial
            doc.setFont(undefined, 'normal')
            doc.setFontSize(11)
            const textLines = doc.splitTextToSize(line, maxWidth)
            doc.text(textLines, margin, yPosition)
            yPosition += textLines.length * 6
          }
        }
        // Ligne normale
        else if (line.trim()) {
          doc.setFont(undefined, 'normal')
          doc.setFontSize(11)
          const cleanLine = line.replace(/\*\*/g, '')
          const textLines = doc.splitTextToSize(cleanLine, maxWidth)
          doc.text(textLines, margin, yPosition)
          yPosition += textLines.length * 6
        } else {
          // Ligne vide
          yPosition += 3
        }
      })

      yPosition += 5
    })

    // Télécharger le PDF
    doc.save(fileName)
  }

  // Envoyer un message
  const sendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || isSending) return

    const token = localStorage.getItem('jwt_token')
    const messageText = inputMessage.trim()
    setInputMessage('')
    setIsSending(true)

    // Si pas de chat actif, créer un nouveau chat
    let chatId = currentChatId
    if (!chatId) {
      chatId = await createNewChat()
      if (!chatId) {
        setIsSending(false)
        setSendingChatId(null)
        alert('Erreur lors de la création du chat')
        return
      }
      setCurrentChatId(chatId)
    }

    // Marquer ce chat comme étant en cours d'envoi
    setSendingChatId(chatId)

    // Ajouter le message utilisateur localement immédiatement
    const userMessage = {
      role: 'user',
      content: { message: messageText },
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      await axios.post(
        `${API_URL}/api/chat/message`,
        {
          chat_id: chatId,
          content: messageText
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Recharger tous les messages depuis le serveur pour obtenir tous les messages (user + assistant(s))
      await loadMessages(chatId)

      // Extraire les réponses de l'assistant pour le PDF
      const allMessages = await axios.get(`${API_URL}/api/chat/${chatId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const messagesData = allMessages.data.messages || []

      // Trouver le dernier message utilisateur et les réponses assistant qui suivent
      const lastUserMsgIndex = messagesData.map(m => m.role).lastIndexOf('user')
      if (lastUserMsgIndex !== -1) {
        const assistantResponses = messagesData
          .slice(lastUserMsgIndex + 1)
          .filter(m => m.role === 'assistant')
          .map(m => m.content.message || m.content.response || '')

        setLastExchange({
          question: messageText,
          responses: assistantResponses,
          timestamp: new Date().toISOString() // Heure actuelle pour un nouveau message
        })

        // Afficher la pop-up PDF pour ce chat spécifique
        setPdfChatId(chatId)
      }

      // Recharger la liste des chats pour mettre à jour le titre
      await loadChats(token)
    } catch (err) {
      console.error('Error sending message:', err)
      alert('Erreur lors de l\'envoi du message')
    } finally {
      setIsSending(false)
      setSendingChatId(null)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('jwt_token')
    setUser(null)
    navigate('/')
  }

  if (loading) {
    return (
      <div className="chat-loading">
        <p>Chargement...</p>
      </div>
    )
  }

  return (
    <div className="chat-page">
      <Header user={user} onLogout={handleLogout} />

      <div className="chat-container">
        {/* Bouton menu mobile */}
        <button
          className="mobile-menu-toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label="Toggle menu"
        >
          {sidebarOpen ? '✕' : '>'}
        </button>

        {/* Overlay pour fermer la sidebar sur mobile */}
        {sidebarOpen && (
          <div
            className="sidebar-overlay"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar avec liste des chats */}
        <div className={`chat-sidebar ${sidebarOpen ? 'open' : ''}`}>
          <button className="btn-new-chat" onClick={startNewChat}>
            + Nouveau Chat
          </button>

          <div className="chat-list">
            {chats.map(chat => (
              <div
                key={chat.id}
                className={`chat-item ${currentChatId === chat.id ? 'active' : ''}`}
                onClick={() => loadMessages(chat.id)}
              >
                <div className="chat-item-title">{chat.title}</div>
                <div className="chat-item-date">
                  {new Date(chat.updated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}, {new Date(chat.updated_at).toLocaleDateString('fr-FR')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Pop-up de téléchargement PDF */}
        {pdfChatId === currentChatId && pdfChatId !== null && (
          <div className="pdf-popup">
            <div className="pdf-popup-content">
              <button className="pdf-popup-close" onClick={() => setPdfChatId(null)}>×</button>
              <p>Votre consultation est prête</p>
              <button className="btn-download-pdf" onClick={generatePDF}>
                Télécharger en PDF
              </button>
            </div>
          </div>
        )}

        {/* Zone de conversation */}
        <div className="chat-main">
          {!currentChatId && (
            <div className="chat-welcome">
              <h2>Bonjour {user?.prenom}</h2>
            </div>
          )}

          <div className="messages-container">
            {messages.map((msg, idx) => {
              // Détecter si c'est un message de débat
              const isDebateMessage = msg.role === 'assistant' && msg.content.intention === 'DEBAT'
              const isCitationMessage = msg.role === 'assistant' && msg.content.intention === 'CITATIONS'
              const messageText = msg.content.message || msg.content.response || ''

              // Détecter le type de message de débat
              const isPourPosition = isDebateMessage && (
                messageText.includes('## Arguments POUR') ||
                messageText.includes('## Réfutation et renforcement POUR')
              )
              const isContraPosition = isDebateMessage && (
                messageText.includes('## Arguments CONTRE') ||
                messageText.includes('## Réfutation et renforcement CONTRE')
              )
              const isPositionsMessage = isDebateMessage && messageText.includes('## Positions du débat')

              // Déterminer l'alignement et la classe
              const messageClass = msg.role === 'user'
                ? 'message-user'
                : isContraPosition
                  ? 'message-debate-contre'
                  : isPourPosition
                    ? 'message-debate-pour'
                    : isPositionsMessage
                      ? 'message-debate-positions'
                      : isCitationMessage
                        ? 'message-citation'
                        : 'message-assistant'

              return (
                <div key={idx} className={`message ${messageClass}`}>
                  {msg.role === 'user' && (
                    <div className="message-header">
                      <strong>Vous</strong>
                    </div>
                  )}
                  <div className="message-content">
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown>{messageText}</ReactMarkdown>
                    ) : (
                      messageText
                    )}
                  </div>
                </div>
              )
            })}
            {isSending && sendingChatId === currentChatId && (
              <div className="message message-assistant loading-message">
                <div className="loading-spinner"></div>
                <span>L'assistant réfléchit...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length === 0 && (
            <form className="message-input-form" onSubmit={sendMessage}>
              <input
                type="text"
                className="message-input"
                placeholder="Posez votre question juridique..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={isSending}
              />
              <button
                type="submit"
                className="btn-send"
                disabled={isSending || !inputMessage.trim()}
                aria-label="Envoyer le message"
              >
                <img src={sendIcon} alt="Envoyer" className="send-icon" />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default Chat
