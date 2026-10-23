
import io

from tools.google_auth import obtenir_service_google
from googleapiclient.http import MediaIoBaseDownload


def _obtenir_service_drive():
    """Obtient le client de l'API Google Drive."""
    return obtenir_service_google("drive", "v3")


def rechercher_fichiers_drive(nom_fichier: str) -> str:
    """
    Recherche des fichiers dans Google Drive par leur nom ou par mot-clé.
    Retourne la liste des fichiers trouvés avec leurs identifiants (IDs).

    Args:
        nom_fichier: Le nom ou une partie du nom du fichier à chercher.
    """
    try:
        service = _obtenir_service_drive()

        # Requête de recherche contenant le nom
        nom_fichier = nom_fichier.replace("\\", "\\\\").replace("'", "\\'")
        query = f"name contains '{nom_fichier}' and trashed = false"

        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=10
        ).execute()

        fichiers = results.get('files', [])

        if not fichiers:
            return (
                f"Aucun fichier contenant '{nom_fichier}' "
                "n'a été trouvé dans votre Google Drive."
            )

        reponse = "Voici les fichiers correspondants trouvés :\n"
        for f in fichiers:
            reponse += (
                f"- **{f['name']}** (MimeType: {f['mimeType']}) "
                f"| ID: `{f['id']}`\n"
            )

        return reponse

    except Exception as e:
        return f"Erreur lors de la recherche Drive : {str(e)}"


def lire_contenu_fichier_drive(id_fichier: str) -> str:
    """
    Récupère et lit le contenu textuel d'un fichier Google Drive
    (fichier texte ou Google Doc) pour permettre à l'agent de
    l'analyser ou de le résumer.

    Args:
        id_fichier: L'identifiant unique (ID) du fichier Google Drive.
    """
    try:
        service = _obtenir_service_drive()

        # 1. Récupérer les métadonnées du fichier
        meta = service.files().get(
            fileId=id_fichier,
            fields="name, mimeType"
        ).execute()

        mime_type = meta.get('mimeType')
        nom = meta.get('name')

        # 2. Cas A : document Google Docs
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(
                fileId=id_fichier,
                mimeType='text/plain'
            )

        # 3. Cas B : fichier texte classique ou JSON
        elif mime_type and (
            'text/' in mime_type or mime_type == 'application/json'
        ):
            request = service.files().get_media(fileId=id_fichier)

        else:
            return (
                f"Le fichier '{nom}' est de type '{mime_type}'. "
                "Ce format n'est pas pris en charge en lecture brute "
                "(uniquement Google Docs et fichiers texte)."
            )

        # 4. Télécharger le contenu en mémoire
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        contenu_texte = fh.getvalue().decode('utf-8', errors='ignore')

        return (
            f"--- Début du contenu de {nom} ---\n"
            f"{contenu_texte}\n"
            f"--- Fin du contenu ---"
        )

    except Exception as e:
        return f"Erreur lors de la lecture du fichier : {str(e)}"
