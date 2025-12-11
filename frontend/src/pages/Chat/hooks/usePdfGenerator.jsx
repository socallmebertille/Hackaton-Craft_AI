import { useState } from 'react'
import { jsPDF } from 'jspdf'

/**
 * Hook personnalisé pour gérer la génération de PDF
 * @returns {Object} État et fonctions de gestion du PDF
 */
export function usePdfGenerator() {
  const [pdfChatId, setPdfChatId] = useState(null)
  const [lastExchange, setLastExchange] = useState(null)

  // Générer un PDF avec la question et les réponses
  const generatePDF = () => {
    if (!lastExchange) return

    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const margin = 15
    const maxWidth = pageWidth - 2 * margin
    let yPosition = 20

    // Date et heure pour le titre et le nom de fichier
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
        // Détecter les lignes avec bullet (•)
        else if (line.startsWith('• ')) {
          const content = line.substring(2)
          const colonIndex = content.indexOf(' : ')

          if (colonIndex > 0) {
            const reference = content.substring(0, colonIndex)
            const explanation = content.substring(colonIndex + 3)

            doc.setFont(undefined, 'bold')
            doc.setFontSize(11)
            const refText = '• ' + reference.replace(/\*\*/g, '') + ' :'
            doc.text(refText, margin, yPosition)
            yPosition += 6

            doc.setFont(undefined, 'normal')
            const explLines = doc.splitTextToSize(explanation, maxWidth - 5)
            doc.text(explLines, margin + 5, yPosition)
            yPosition += explLines.length * 6 + 2
          } else {
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
          yPosition += 3
        }
      })

      yPosition += 5
    })

    doc.save(fileName)
  }

  return {
    pdfChatId,
    setPdfChatId,
    lastExchange,
    setLastExchange,
    generatePDF
  }
}
