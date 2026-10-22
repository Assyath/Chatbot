from tools.drive_tool import rechercher_fichiers_drive

from .meteo import obtenir_meteo
from .recherche import recherche_web
from .notion_tool import ajouter_note_notion
from .send_mail import envoyer_email
from .calendar_tool import (
    lister_evenements_calendar,
    creer_evenement_calendar,
    modifier_evenement_calendar,
    supprimer_evenement_calendar
)

from .drive_tool import rechercher_fichiers_drive, lire_contenu_fichier_drive

ALL_TOOLS = [
    obtenir_meteo,
    recherche_web,
    ajouter_note_notion,
    envoyer_email,
    lister_evenements_calendar,
    creer_evenement_calendar,
    modifier_evenement_calendar,
    supprimer_evenement_calendar,
    rechercher_fichiers_drive,
    lire_contenu_fichier_drive
]