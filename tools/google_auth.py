
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


ROOT_DIR = Path(__file__).resolve().parent.parent

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.readonly",
]


def obtenir_google_credentials():
    """Charge les identifiants Google depuis Render ou les fichiers locaux."""
    token_path = ROOT_DIR / "token.json"
    credentials_path = ROOT_DIR / "credentials.json"

    token_env = os.getenv("GOOGLE_TOKEN_JSON")

    if token_env:
        try:
            info = json.loads(token_env)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "La variable GOOGLE_TOKEN_JSON ne contient pas un JSON valide."
            ) from exc

        creds = Credentials.from_authorized_user_info(info, SCOPES)

    elif token_path.exists():
        creds = Credentials.from_authorized_user_file(
            str(token_path), SCOPES
        )

    else:
        creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

        # En local, sauvegarder le jeton renouvelé.
        # Sur Render, ne pas écrire dans les variables d'environnement.
        if not token_env:
            token_path.write_text(creds.to_json(), encoding="utf-8")

        return creds

    # Le flux interactif n'est autorisé qu'en environnement local.
    if os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"):
        raise RuntimeError(
            "Authentification Google absente ou expirée sur Render. "
            "Vérifiez GOOGLE_TOKEN_JSON et autorisez à nouveau le compte "
            "Google si nécessaire."
        )

    if not credentials_path.exists():
        raise FileNotFoundError(
            "Le fichier credentials.json est absent à la racine du projet."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), SCOPES
    )
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def obtenir_service_google(api_name: str, version: str):
    creds = obtenir_google_credentials()
    return build(api_name, version, credentials=creds)
