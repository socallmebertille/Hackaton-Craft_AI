"""
Utilitaires pour générer des PDF de débats
"""
import re
from io import BytesIO
from datetime import datetime
from fastapi.responses import Response

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, darkgreen, darkred


def format_markdown_to_html(text: str) -> str:
    """
    Convertit le texte markdown en HTML pour un seul bloc de texte avec formatage

    Gère:
    - Titres (# ## ###)
    - Listes numérotées avec indentation
    - Formatage gras (**texte**) et italique (*texte*)
    - Sauts de ligne appropriés
    """

    def convert_markdown_formatting(line: str) -> str:
        """Convertit le formatage markdown en HTML pour ReportLab"""
        # Gérer le gras **texte**
        line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
        # Gérer l'italique *texte*
        line = re.sub(r'(?<!</b>)\*(.+?)\*(?!<b>)', r'<i>\1</i>', line)
        return line

    lines = text.split('\n')
    html_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append('<br/>')
            continue

        # Gérer les titres
        if line.startswith('### '):
            title_text = convert_markdown_formatting(line[4:].strip())
            html_parts.append(f'<br/><b><font size="12">{title_text}</font></b><br/>')
        elif line.startswith('## '):
            title_text = convert_markdown_formatting(line[3:].strip())
            html_parts.append(f'<br/><b><font size="13">{title_text}</font></b><br/>')
        elif line.startswith('# '):
            title_text = convert_markdown_formatting(line[2:].strip())
            html_parts.append(f'<br/><b><font size="14">{title_text}</font></b><br/>')
        # Gérer les listes numérotées (1., 2., etc.)
        elif line[0].isdigit() and '. ' in line[:4]:
            formatted_line = convert_markdown_formatting(line)
            # Ajouter une indentation pour les listes
            html_parts.append(f'&nbsp;&nbsp;&nbsp;&nbsp;{formatted_line}<br/>')
        else:
            # Paragraphe normal
            formatted_line = convert_markdown_formatting(line)
            html_parts.append(f'{formatted_line}<br/>')

    return ''.join(html_parts)


def generate_debate_pdf(debate: dict) -> Response:
    """
    Génère un PDF professionnel pour un débat terminé

    Args:
        debate (dict): Données du débat avec question, rounds, summary

    Returns:
        Response: Réponse FastAPI avec le PDF en attachement
    """
    # Créer un buffer en mémoire pour le PDF
    buffer = BytesIO()

    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1*inch,
        bottomMargin=1*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )

    # Obtenir les styles de base
    styles = getSampleStyleSheet()

    # Créer des styles personnalisés avec couleurs
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor="#764ba2",
        spaceAfter=20,
        alignment=1  # Centré
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=black,
        spaceAfter=12,
        spaceBefore=20
    )

    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor="#2a40a3",
        leftIndent=20,
        rightIndent=20,
        spaceAfter=15,
        borderWidth=1,
        borderColor="#667de8",
        borderPadding=10
    )

    # Style pour arguments POUR (vert)
    argument_pour_style = ParagraphStyle(
        'ArgumentPour',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=15,
        spaceAfter=15,
        textColor=darkgreen,
        borderWidth=1,
        borderColor="#28a745",
        borderPadding=8
    )

    # Style pour arguments CONTRE (rouge)
    argument_contre_style = ParagraphStyle(
        'ArgumentContre',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=15,
        spaceAfter=15,
        textColor=darkred,
        borderWidth=1,
        borderColor="#dc3545",
        borderPadding=8
    )

    # Style pour la synthèse finale (bleu comme la question)
    summary_style = ParagraphStyle(
        'SummaryStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor="#2a40a3",
        leftIndent=20,
        rightIndent=20,
        spaceAfter=15,
        borderWidth=1,
        borderColor="#667de8",
        borderPadding=10
    )

    # Construire le contenu du PDF
    story = []

    # Titre principal
    story.append(Paragraph("DÉBAT JURIDIQUE CONTRADICTOIRE", title_style))
    story.append(Spacer(1, 12))

    # Date uniquement (sans ID du débat)
    now = datetime.now()
    date_info = f"Généré le {now.strftime('%d/%m/%Y à %H:%M')}"
    story.append(Paragraph(date_info, styles['Normal']))
    story.append(Spacer(1, 20))

    # Question
    story.append(Paragraph("QUESTION POSÉE", subtitle_style))
    story.append(Paragraph(debate["question"], question_style))

    # Arguments du débat
    if debate.get("debate_rounds"):
        for round_data in debate["debate_rounds"]:
            round_num = round_data.get("round", "")
            position = round_data.get("position", "")
            argument = round_data.get("argument", "")

            # Formatage par round avec couleurs - UN SEUL ENCADRÉ PAR ROUND
            if position == "pour":
                story.append(Spacer(1, 15))
                story.append(Paragraph(f"<b>ARGUMENT POUR - Round {round_num}</b>", subtitle_style))
                # Convertir tout le contenu markdown en HTML et créer un seul Paragraph
                html_content = format_markdown_to_html(argument)
                story.append(Paragraph(html_content, argument_pour_style))
            elif position == "contre":
                story.append(Spacer(1, 15))
                story.append(Paragraph(f"<b>ARGUMENT CONTRE - Round {round_num}</b>", subtitle_style))
                # Convertir tout le contenu markdown en HTML et créer un seul Paragraph
                html_content = format_markdown_to_html(argument)
                story.append(Paragraph(html_content, argument_contre_style))

            story.append(Spacer(1, 10))

    # Synthèse finale - EN BLEU COMME LA QUESTION
    if debate.get("summary"):
        story.append(Spacer(1, 20))
        story.append(Paragraph("SYNTHÈSE FINALE", subtitle_style))
        story.append(Spacer(1, 10))

        # Convertir le markdown en HTML et créer un seul Paragraph avec style bleu
        html_content = format_markdown_to_html(debate["summary"])
        story.append(Paragraph(html_content, summary_style))

    # Générer le PDF
    doc.build(story)

    # Récupérer le contenu du buffer
    pdf_data = buffer.getvalue()
    buffer.close()

    # Créer le nom de fichier
    filename = f"debat-juridique-{now.strftime('%Y%m%d-%H%M%S')}.pdf"

    # Retourner la réponse avec le PDF
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
