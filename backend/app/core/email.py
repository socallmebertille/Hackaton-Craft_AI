"""
Service d'envoi d'emails via SMTP
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from typing import List


async def send_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    text_content: str = None
):
    """
    Envoie un email via SMTP

    Args:
        to_emails: Liste des destinataires
        subject: Sujet de l'email
        html_content: Contenu HTML de l'email
        text_content: Contenu texte alternatif (optionnel)

    Raises:
        Exception: Si l'envoi échoue
    """
    if not settings.SMTP_HOST:
        print("⚠️ SMTP non configuré - Email non envoyé")
        print(f"Destinataire: {to_emails}")
        print(f"Sujet: {subject}")
        print(f"Contenu: {html_content[:200]}...")
        return

    # Créer le message
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject

    # Ajouter le contenu texte si fourni
    if text_content:
        part_text = MIMEText(text_content, "plain")
        message.attach(part_text)

    # Ajouter le contenu HTML
    part_html = MIMEText(html_content, "html")
    message.attach(part_html)

    try:
        # Envoyer l'email
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        print(f"✅ Email envoyé à {to_emails}")
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        raise Exception(f"Erreur lors de l'envoi de l'email: {str(e)}")


def generate_verification_email(email: str, verification_token: str) -> tuple[str, str]:
    """
    Génère le contenu HTML et texte pour l'email de vérification

    Args:
        email: Email de l'utilisateur
        verification_token: Token de vérification

    Returns:
        tuple: (html_content, text_content)
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #667eea; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MIBS AI</h1>
            </div>
            <div class="content">
                <h2>Vérifiez votre adresse email</h2>
                <p>Bonjour,</p>
                <p>Merci de vous être inscrit sur MIBS AI. Pour activer votre compte, veuillez vérifier votre adresse email en cliquant sur le bouton ci-dessous :</p>
                <center>
                    <a href="{verification_url}" class="button">Vérifier mon email</a>
                </center>
                <p>Si le bouton ne fonctionne pas, vous pouvez copier et coller ce lien dans votre navigateur :</p>
                <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                <p><strong>Ce lien est valide pendant 24 heures.</strong></p>
                <p>Si vous n'avez pas créé de compte, vous pouvez ignorer cet email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 MIBS AI. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Bienvenue sur Juridique AI !

    Merci de vous être inscrit. Pour activer votre compte, veuillez vérifier votre adresse email en cliquant sur le lien ci-dessous :

    {verification_url}

    Ce lien est valide pendant 24 heures.

    Si vous n'avez pas créé de compte, vous pouvez ignorer cet email.

    ---
    Juridique AI - MIBS
    """

    return html_content, text_content


def generate_account_approved_email(prenom: str, nom: str) -> tuple[str, str]:
    """
    Génère le contenu HTML et texte pour l'email d'approbation du compte

    Args:
        prenom: Prénom de l'utilisateur
        nom: Nom de l'utilisateur

    Returns:
        tuple: (html_content, text_content)
    """
    login_url = f"{settings.FRONTEND_URL}/"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #667eea; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .success {{ background: #22c55e; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✓ Compte activé</h1>
            </div>
            <div class="content">
                <div class="success">
                    <h2 style="margin: 0;">Votre compte a été approuvé</h2>
                </div>
                <p>Bonjour {prenom} {nom},</p>
                <p>Nous avons le plaisir de vous informer que votre compte MIBS AI a été <strong>approuvé et activé</strong> par notre équipe.</p>
                <p>Vous pouvez dès maintenant vous connecter et profiter de tous les services de notre plateforme :</p>
                <center>
                    <a href="{login_url}" class="button">Se connecter</a>
                </center>
                <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
                <p>Bienvenue sur MIBS AI !</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 MIBS AI. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    ✓ Compte activé !

    Bonjour {prenom} {nom},

    Nous avons le plaisir de vous informer que votre compte Juridique AI a été approuvé et activé par notre équipe.

    Vous pouvez dès maintenant vous connecter et profiter de tous les services de notre plateforme :
    - Analyse juridique automatique
    - Débat contradictoire IA
    - Accès à la base Légifrance

    Connectez-vous ici : {login_url}

    Bienvenue sur Juridique AI !

    ---
    Juridique AI - MIBS
    """

    return html_content, text_content
