import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Configuration validée par le test réussi
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Port TLS standard
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def envoyer_email(destinataire: str, objet: str, contenu: str) -> str:
    """
    Envoie un email réel via le serveur SMTP de Gmail en mode sécurisé TLS.
    
    IMPORTANT : Cet outil ne doit être déclenché QUE si l'utilisateur a expressément
    donné sa confirmation et son accord pour procéder à l'envoi de ce message spécifique.
    
    Args:
        destinataire: L'adresse email de la personne qui reçoit le message.
        objet: Le sujet de l'email.
        contenu: Le corps du message (le texte de l'email).
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return "Erreur : Les identifiants SMTP (SMTP_EMAIL ou SMTP_PASSWORD) ne sont pas configurés dans le fichier .env."

    try:
        # Configuration du message
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = destinataire
        msg['Subject'] = objet
        
        # Ajout du contenu textuel en UTF-8
        msg.attach(MIMEText(contenu, 'plain', 'utf-8'))
        
        # Connexion sécurisée TLS (Validée par test_mail.py)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Sécurisation de la connexion requise par Gmail sur le port 587
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, destinataire, msg.as_string())
            
        return f"Succès : L'email a bien été envoyé à {destinataire} !"
        
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email : {str(e)}"
