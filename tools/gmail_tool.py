
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

from tools.google_auth import obtenir_service_google


def envoyer_email(destinataire: str, objet: str, contenu: str) -> str:
    """Envoie un e-mail via Gmail API."""

    try:
        service = obtenir_service_google("gmail", "v1")

        message = MIMEMultipart()
        message["to"] = destinataire
        message["subject"] = objet
        message.attach(MIMEText(contenu, "plain", "utf-8"))

        message_encode = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        resultat = service.users().messages().send(
            userId="me",
            body={"raw": message_encode}
        ).execute()

        return f"E-mail envoyé avec succès à {destinataire}."

    except Exception as e:
        return f"Erreur lors de l'envoi de l'e-mail : {e}"
