import { useState, useCallback } from 'react'
import axios from 'axios'
import { API_URL } from '../../../config/api'

/**
 * Hook personnalisé pour gérer la logique des chats et messages
 * @returns {Object} État et fonctions de gestion des chats
 */
export function useChat() {
  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isSending, setIsSending] = useState(false)
  const [sendingChatId, setSendingChatId] = useState(null)
  const [hasActiveRequest, setHasActiveRequest] = useState(false)

  // Charger la liste des chats
  const loadChats = useCallback(async (token) => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/list`, {
        headers: { Authorization: `Bearer ${token || localStorage.getItem('jwt_token')}` }
      })
      setChats(response.data.chats || [])
    } catch (err) {
      console.error('Error loading chats:', err)
    }
  }, [])

  // Charger les messages d'un chat
  const loadMessages = useCallback(async (chatId) => {
    const token = localStorage.getItem('jwt_token')
    try {
      const response = await axios.get(`${API_URL}/api/chat/${chatId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const messagesData = response.data.messages || []
      setMessages(messagesData)
      setCurrentChatId(chatId)

      // Vérifier si ce chat avait une requête active et si elle est complétée
      const activeChatId = localStorage.getItem('activeChatRequest')
      if (activeChatId === chatId && messagesData.length > 0) {
        const lastMessage = messagesData[messagesData.length - 1]
        if (lastMessage.role === 'assistant') {
          localStorage.removeItem('activeChatRequest')
          setHasActiveRequest(false)
        }
      }

      return messagesData
    } catch (err) {
      console.error('Error loading messages:', err)
      return []
    }
  }, [])

  // Créer un nouveau chat
  const createNewChat = useCallback(async () => {
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
  }, [loadChats])

  // Réinitialiser pour un nouveau chat
  const startNewChat = useCallback(() => {
    setCurrentChatId(null)
    setMessages([])
  }, [])

  // Envoyer un message
  const sendMessage = useCallback(async (messageText, onSuccess) => {
    const token = localStorage.getItem('jwt_token')
    setIsSending(true)

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

    setSendingChatId(chatId)
    setHasActiveRequest(true)
    localStorage.setItem('activeChatRequest', chatId)

    // Ajouter le message utilisateur localement
    const userMessage = {
      role: 'user',
      content: { message: messageText },
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      await axios.post(
        `${API_URL}/api/chat/message`,
        { chat_id: chatId, content: messageText },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      const messagesData = await loadMessages(chatId)

      // Appeler le callback de succès avec les messages
      if (onSuccess) {
        onSuccess(messagesData, messageText)
      }

      await loadChats(token)

      localStorage.removeItem('activeChatRequest')
      setHasActiveRequest(false)
    } catch (err) {
      console.error('Error sending message:', err)
      alert('Erreur lors de l\'envoi du message')
      localStorage.removeItem('activeChatRequest')
      setHasActiveRequest(false)
    } finally {
      setIsSending(false)
      setSendingChatId(null)
    }
  }, [currentChatId, createNewChat, loadMessages, loadChats])

  // Vérifier si une requête active a reçu sa réponse
  const checkActiveRequest = useCallback(async (chatId, token) => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/${chatId}/messages`, {
        headers: { Authorization: `Bearer ${token || localStorage.getItem('jwt_token')}` }
      })
      const messagesData = response.data.messages || []

      if (messagesData.length > 0) {
        const lastMessage = messagesData[messagesData.length - 1]
        if (lastMessage.role === 'assistant') {
          localStorage.removeItem('activeChatRequest')
          setHasActiveRequest(false)
          setIsSending(false)
          setSendingChatId(null)
        } else {
          setHasActiveRequest(true)
          setIsSending(true)
          setSendingChatId(chatId)
          setCurrentChatId(chatId)
          await loadMessages(chatId)
        }
      }
    } catch (err) {
      console.error('Error checking active request:', err)
      localStorage.removeItem('activeChatRequest')
      setHasActiveRequest(false)
      setIsSending(false)
      setSendingChatId(null)
    }
  }, [loadMessages])

  return {
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
    createNewChat,
    startNewChat,
    sendMessage,
    checkActiveRequest
  }
}
