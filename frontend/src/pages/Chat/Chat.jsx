import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import Header from '../../components/layout/Header'
import ChatSidebar from './components/ChatSidebar'
import MessageList from './components/MessageList'
import MessageInput from './components/MessageInput'
import PdfPopup from './components/PdfPopup'
import { useChat } from './hooks/useChat'
import { useChatPolling } from './hooks/useChatPolling'
import { usePdfGenerator } from './hooks/usePdfGenerator'
import '../../styles/chat/index.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Chat() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [inputMessage, setInputMessage] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const messagesEndRef = useRef(null)

  // Custom hooks
  const {
    chats,
    currentChatId,
    messages,
    isSending,
    sendingChatId,
    hasActiveRequest,
    setMessages,
    setHasActiveRequest,
    setIsSending,
    setSendingChatId,
    loadChats,
    loadMessages,
    startNewChat,
    sendMessage: sendChatMessage,
    checkActiveRequest
  } = useChat()

  const { pdfChatId, setPdfChatId, lastExchange, setLastExchange, generatePDF } = usePdfGenerator()

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Callback pour le polling
  const handleMessageReceived = useCallback(async (messagesData, token) => {
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
          timestamp: userMessage.created_at
        })
        setPdfChatId(currentChatId)
      }
    }

    localStorage.removeItem('activeChatRequest')
    setHasActiveRequest(false)
    setIsSending(false)
    setSendingChatId(null)

    await loadChats(token)
  }, [currentChatId, setPdfChatId, setLastExchange, setHasActiveRequest, setIsSending, setSendingChatId, loadChats])

  // Polling automatique
  useChatPolling(hasActiveRequest, currentChatId, loadMessages, handleMessageReceived)

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

        // Vérifier s'il y a une requête active en cours
        const activeChatId = localStorage.getItem('activeChatRequest')
        if (activeChatId) {
          await checkActiveRequest(activeChatId, token)
        }
      } catch (err) {
        console.error('Auth error:', err)
        localStorage.removeItem('jwt_token')
        navigate('/')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [navigate, loadChats, checkActiveRequest])

  // Gestion de l'envoi de message
  const handleSendMessage = (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || isSending) return

    const messageText = inputMessage.trim()
    setInputMessage('')

    sendChatMessage(messageText, (messagesData, messageText) => {
      // Callback après envoi réussi
      const lastUserMsgIndex = messagesData.map(m => m.role).lastIndexOf('user')
      if (lastUserMsgIndex !== -1) {
        const assistantResponses = messagesData
          .slice(lastUserMsgIndex + 1)
          .filter(m => m.role === 'assistant')
          .map(m => m.content.message || m.content.response || '')

        setLastExchange({
          question: messageText,
          responses: assistantResponses,
          timestamp: new Date().toISOString()
        })

        setPdfChatId(currentChatId)
      }
    })
  }

  const handleStartNewChat = () => {
    startNewChat()
    setPdfChatId(null)
  }

  const handleSelectChat = (chatId) => {
    loadMessages(chatId)
    setSidebarOpen(false)
  }

  const handleLogout = () => {
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('activeChatRequest')
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

        <ChatSidebar
          chats={chats}
          currentChatId={currentChatId}
          hasActiveRequest={hasActiveRequest}
          isSending={isSending}
          sidebarOpen={sidebarOpen}
          onStartNewChat={handleStartNewChat}
          onSelectChat={handleSelectChat}
          onToggleSidebar={() => setSidebarOpen(false)}
        />

        <PdfPopup
          show={pdfChatId === currentChatId && pdfChatId !== null}
          onClose={() => setPdfChatId(null)}
          onDownload={generatePDF}
        />

        {/* Zone de conversation */}
        <div className="chat-main">
          {!currentChatId && (
            <div className="chat-welcome">
              <h2>Bonjour {user?.prenom}</h2>
            </div>
          )}

          <MessageList
            messages={messages}
            isSending={isSending}
            sendingChatId={sendingChatId}
            currentChatId={currentChatId}
            messagesEndRef={messagesEndRef}
          />

          {messages.length === 0 && (
            <MessageInput
              inputMessage={inputMessage}
              isSending={isSending}
              hasActiveRequest={hasActiveRequest}
              onInputChange={(e) => setInputMessage(e.target.value)}
              onSubmit={handleSendMessage}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default Chat
