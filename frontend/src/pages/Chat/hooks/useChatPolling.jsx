import { useEffect } from 'react'
import axios from 'axios'
import { API_URL } from '../../../config/api'

/**
 * Hook personnalisé pour le polling automatique des messages
 * Vérifie toutes les 3 secondes si de nouveaux messages sont arrivés
 * @param {boolean} hasActiveRequest - Si une requête est active
 * @param {string} currentChatId - ID du chat actif
 * @param {string} sendingChatId - ID du chat en cours d'envoi (utilisé pour les nouveaux chats)
 * @param {Function} loadMessages - Fonction pour charger les messages
 * @param {Function} onMessageReceived - Callback quand les messages arrivent
 */
export function useChatPolling(hasActiveRequest, currentChatId, sendingChatId, loadMessages, onMessageReceived) {
  useEffect(() => {
    // Utiliser sendingChatId en priorité pour gérer les nouveaux chats
    const chatIdToUse = sendingChatId || currentChatId
    if (!hasActiveRequest || !chatIdToUse) return

    const checkForMessages = async () => {
      const token = localStorage.getItem('jwt_token')
      try {
        const response = await axios.get(`${API_URL}/api/chat/${chatIdToUse}/messages`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const messagesData = response.data.messages || []

        if (messagesData.length > 0) {
          const lastMessage = messagesData[messagesData.length - 1]
          if (lastMessage.role === 'assistant') {
            // Réponse arrivée
            await loadMessages(chatIdToUse)

            // Appeler le callback avec les nouvelles données
            if (onMessageReceived) {
              onMessageReceived(messagesData, token)
            }
          } else {
            // Toujours en attente, mettre à jour les messages au cas où
            // Note: setMessages est géré dans le composant parent
          }
        }
      } catch (err) {
        console.error('Error polling messages:', err)
      }
    }

    // Vérifier toutes les 3 secondes
    const interval = setInterval(checkForMessages, 3000)

    return () => clearInterval(interval)
  }, [hasActiveRequest, currentChatId, sendingChatId, loadMessages, onMessageReceived])
}
