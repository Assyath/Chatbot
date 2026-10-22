import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Portée d'accès (Scope) requise pour lire et modifier le calendrier
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def _obtenir_service_calendar():
    """Fonction interne pour authentifier et obtenir le client de l'API Google Calendar."""
    creds = None
    # Le fichier token.json stocke les privilèges d'accès utilisateur de manière permanente
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # Si le jeton n'est pas valide ou inexistant, on lance le flux de connexion par navigateur
        # Si le jeton n'est pas valide ou inexistant, on lance le flux de connexion
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Erreur : Le fichier 'credentials.json' est absent à la racine du projet.")
            
            # Utilisation du flux natif 
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # Ou flow.run_console() 
            
        # Sauvegarde du jeton à l'aide de l'API fournie par Credentials.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


    return build('calendar', 'v3', credentials=creds)


def lister_evenements_calendar(date_debut_iso: str = None, date_fin_iso: str = None) -> str:
    """
    Affiche ou recherche les événements à venir de l'agenda de l'utilisateur.
    Permet aussi de filtrer par date ou période spécifique.
    
    Args:
        date_debut_iso: Optionnel. Date de début au format ISO (ex: '2026-10-23T00:00:00Z').
                        Si absent, utilise l'instant présent par défaut.
        date_fin_iso: Optionnel. Date de fin au format ISO (ex: '2026-10-24T23:59:59Z').
    """
    try:
        service = _obtenir_service_calendar()
        
        # Temps par défaut : maintenant
        t_debut = date_debut_iso if date_debut_iso else datetime.datetime.utcnow().isoformat() + 'Z'
        
        # Appel à l'API Google Calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=t_debut,
            timeMax=date_fin_iso,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "Aucun événement trouvé pour la période demandée."

        resultat = "Voici vos événements :\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            resultat += f"- **{event['summary']}** : le {start} (ID: {event['id']})\n"
        return resultat

    except Exception as e:
        return f"Erreur lors de la lecture de l'agenda : {str(e)}"


def creer_evenement_calendar(titre: str, date_debut_iso: str, date_fin_iso: str, description: str = None) -> str:
    """
    Crée un nouvel événement sur l'agenda de l'utilisateur.
    
    Args:
        titre: Le nom ou résumé de l'événement (ex: 'Réunion Projet').
        date_debut_iso: Date et heure de début en format ISO avec fuseau (ex: '2026-10-23T10:00:00+01:00').
        date_fin_iso: Date et heure de fin en format ISO avec fuseau (ex: '2026-10-23T11:00:00+01:00').
        description: Optionnel. Détails ou notes sur la réunion.
    """
    try:
        service = _obtenir_service_calendar()
        
        event = {
            'summary': titre,
            'description': description,
            'start': {'dateTime': date_debut_iso, 'timeZone': 'Africa/Porto-Novo'},
            'end': {'dateTime': date_fin_iso, 'timeZone': 'Africa/Porto-Novo'},
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Succès : L'événement '{titre}' a été planifié avec succès ! (Lien : {created_event.get('htmlLink')})"

    except Exception as e:
        return f"Erreur lors de la création de l'événement : {str(e)}"


def modifier_evenement_calendar(id_evenement: str, nouveau_titre: str = None, nouvelle_date_debut_iso: str = None, nouvelle_date_fin_iso: str = None) -> str:
    """
    Modifie un événement existant dans l'agenda.
    ATTENTION : Cet outil exige l'accord explicite préalable de l'utilisateur.
    """
    try:
        service = _obtenir_service_calendar()
        # Récupération du bloc existant
        event = service.events().get(calendarId='primary', eventId=id_evenement).execute()
        
        if nouveau_titre:
            event['summary'] = nouveau_titre
        if nouvelle_date_debut_iso:
            event['start']['dateTime'] = nouvelle_date_debut_iso
        if nouvelle_date_fin_iso:
            event['end']['dateTime'] = nouvelle_date_fin_iso

        updated_event = service.events().update(calendarId='primary', eventId=id_evenement, body=event).execute()
        return f"Succès : L'événement a bien été modifié (Mis à jour : {updated_event.get('summary')})."
    except Exception as e:
        return f"Erreur lors de la modification : {str(e)}"


def supprimer_evenement_calendar(id_evenement: str) -> str:
    """
    Supprime définitivement un événement de l'agenda de l'utilisateur.
    ATTENTION : Cet outil exige l'accord explicite préalable de l'utilisateur.
    """
    try:
        service = _obtenir_service_calendar()
        service.events().delete(calendarId='primary', eventId=id_evenement).execute()
        return "Succès : L'événement a été supprimé définitivement de votre agenda."
    except Exception as e:
        return f"Erreur lors de la suppression : {str(e)}"
