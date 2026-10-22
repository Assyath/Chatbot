from datetime import datetime
import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from tools import ALL_TOOLS

load_dotenv()

# --- Modèles  ---
provider = OpenAIProvider(
    base_url="https://api.rodiumai.io/v1",
    api_key=os.environ["RODIUMAI_API_KEY"],
)
gpt_model = OpenAIChatModel("openai/gpt-4o-mini", provider=provider)
haiku_model = OpenAIChatModel("anthropic/claude-haiku-4-5-20251001", provider=provider)

# --- Agent ---
# --- Agent ---
agent = Agent(
    gpt_model,
    instructions=(
        "Tu es un assistant personnel. Réponds en français. "
        "Utilise les outils disponibles quand la demande l'exige. "
        f"Pour information, la date et l'heure actuelle sont : {datetime.now().isoformat()}.\n\n"
        
        # Directives strictes pour l'outil Email :
        "CONSIGNES POUR L'ENVOI D'EMAILS :\n"
        "1. Si l'utilisateur demande d'envoyer un email, assure-toi d'avoir 3 informations : le destinataire, l'objet et le contenu.\n"
        "2. Si une information est manquante, pose poliment des questions pour l'obtenir.\n"
        "3. Une fois les informations complètes, présente CLAIREMENT le brouillon à l'utilisateur (Destinataire, Objet, Contenu) et demande-lui sa CONFIRMATION explicite (ex: 'Confirmez-vous l'envoi ?').\n"
        "4. Ne déclenche JAMAIS l'outil 'envoyer_email' tant que l'utilisateur n'a pas répondu par un oui clair ou une confirmation explicite."
       
        "CONSIGNES POUR L'AGENDA GOOGLE :\n"
        "1. Pour lister ou rechercher des rendez-vous, convertis toujours les demandes de l'utilisateur en dates ISO adaptées.\n"
        "2. Pour la création, demande l'heure et la date précises si elles manquent.\n"
        "3. Pour MODIFIER ou SUPPRIMER un événement, tu dois d'abord lister les événements pour trouver l'ID de l'événement cible. "
        "Ensuite, présente le changement à l'utilisateur et n'appelle l'outil qu'APRÈS avoir obtenu une CONFIRMATION et un accord explicite."

        "CONSIGNES POUR GOOGLE DRIVE :\n"
        "1. Si l'utilisateur cherche un document, utilise 'rechercher_fichiers_drive' avec des mots-clés pertinents.\n"
        "2. Si l'utilisateur demande de résumer, analyser ou répondre à une question sur un document, utilise d'abord la recherche pour trouver son ID, puis utilise 'lire_contenu_fichier_drive' pour extraire son texte avant de formuler ta réponse."

   ),

    tools=ALL_TOOLS,
)

# --- Interface web de chat ---
app = agent.to_web(
    models={
        "GPT-4o Mini": gpt_model,
        "Claude 4.5 Haiku": haiku_model,
    },
)