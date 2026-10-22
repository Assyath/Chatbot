import os
from importlib import import_module
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client 

# Chargement des variables d'environnement (.env)
load_dotenv()

# Récupération des accès sécurisés de l'intégration privée
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")

def ajouter_note_notion(contenu: str) -> str:
    """
    Ajoute un nouveau paragraphe de texte à la suite du contenu existant 
    sur la page Notion connectée, précédé de la date et de l'heure.
    
    Args:
        contenu: Le message ou la note à ajouter dans Notion.
    """
    # Validation de la présence des configurations requises
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        return "Erreur : Les identifiants Notion (NOTION_TOKEN ou NOTION_PAGE_ID) sont manquants dans le fichier .env."

    try:
        # Initialisation du client officiel qui communique avec l'API Notion
        try:
            Client = import_module("notion_client").Client
        except ImportError:
            return "Erreur : Le package notion-client est absent. Installez-le avec 'pip install notion-client'."

        notion = Client(auth=NOTION_TOKEN)
        
        # Ajout d'un horodatage pour séparer proprement les notes chronologiquement
        horodatage = datetime.now().strftime("[%d/%m/%Y %H:%M]")
        texte_final = f"{horodatage} {contenu}"
        
        # Appel de l'API Notion pour ajouter (append) 
        notion.blocks.children.append(
            block_id=NOTION_PAGE_ID,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": texte_final
                                }
                            }
                        ]
                    }
                }
            ]
        )
        return "Succès : La note a bien été ajoutée à la suite sur votre page Notion !"
        
    except Exception as e:
        # Capture et retour des erreurs de l'API (ex: mauvais Token, page non partagée, etc.)
        return f"Erreur lors de l'appel à l'API Notion : {str(e)}"
