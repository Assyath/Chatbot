import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.readonly'  # Droit de lecture seule pour le Drive
]

def _obtenir_service_drive():
    """Fonction interne pour authentifier et obtenir le client de l'API Google Drive."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Erreur : Le fichier 'credentials.json' est absent.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def rechercher_fichiers_drive(nom_fichier: str) -> str:
    """
    Recherche des fichiers dans Google Drive par leur nom ou par mot-clé.
    Retourne la liste des fichiers trouvés avec leurs identifiants (IDs).
    
    Args:
        nom_fichier: Le nom ou une partie du nom du fichier à chercher.
    """
    try:
        service = _obtenir_service_drive()
        
        # Requête de recherche insensible à la casse contenant le nom
        query = f"name contains '{nom_fichier}' and trashed = false"
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=10
        ).execute()
        
        fichiers = results.get('files', [])
        
        if not fichiers:
            return f"Aucun fichier contenant '{nom_fichier}' n'a été trouvé dans votre Google Drive."
            
        reponse = f"Voici les fichiers correspondants trouvés :\n"
        for f in fichiers:
            reponse += f"- **{f['name']}** (MimeType: {f['mimeType']}) | ID: `{f['id']}`\n"
        return reponse

    except Exception as e:
        return f"Erreur lors de la recherche Drive : {str(e)}"


def lire_contenu_fichier_drive(id_fichier: str) -> str:
    """
    Récupère et lit le contenu textuel d'un fichier Google Drive (Fichier texte ou Google Doc)
    pour permettre à l'agent de l'analyser ou de le résumer.
    
    Args:
        id_fichier: L'identifiant unique (ID) du fichier Google Drive.
    """
    try:
        service = _obtenir_service_drive()
        
        # 1. Récupérer les métadonnées pour connaître le type de fichier (MimeType)
        meta = service.files().get(fileId=id_fichier, fields="name, mimeType").execute()
        mime_type = meta.get('mimeType')
        nom = meta.get('name')
        
        # 2. Cas A : C'est un Google Doc officiel -> On l'exporte en texte brut
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId=id_fichier, mimeType='text/plain')
        # 3. Cas B : Un fichier texte classique ou markdown
        elif 'text/' in mime_type or mime_type == 'application/json':
            request = service.files().get_media(fileId=id_fichier)
        else:
            return f"Le fichier '{nom}' est de type '{mime_type}'. Ce format n'est pas pris en charge en lecture brute (uniquement Google Docs et fichiers texte)."

        # Téléchargement du contenu en mémoire
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        contenu_texte = fh.getvalue().decode('utf-8', errors='ignore')
        return f"--- Début du contenu de {nom} ---\n{contenu_texte}\n--- Fin du contenu ---"

    except Exception as e:
        return f"Erreur lors de la lecture du fichier : {str(e)}"
