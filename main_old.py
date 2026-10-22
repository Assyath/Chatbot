import os
from datetime import datetime
import httpx
import json
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Conversation, Message
from fastapi.responses import StreamingResponse

load_dotenv()

RODIUMAI_URL = "https://api.rodiumai.io/v1/chat/completions"
RODIUMAI_API_KEY = os.environ["RODIUMAI_API_KEY"]

# Liste des modèles officiellement autorisés par le serveur
ALLOWED_MODELS = {
    "openai/gpt-4o-mini": "GPT-4o Mini (Par défaut)",
    "anthropic/claude-haiku-4-5-20251001": "Claude 4.5 Haiku"
}

# Le modèle par défaut si rien n'est sélectionné
DEFAULT_MODEL = "openai/gpt-4o-mini"

PREVIEW_LENGTH = 60

# Roles the LLM understands
LLM_ROLES = {"user", "assistant"}
NOTIFICATION_ROLE = "system-notification"
NOTE_ROLE = "note"
NOTIFICATION_EVERY = 10  
NOTIFICATION_TEXT = "Notification système : Une dizaine de messages écrits."

# Configuration de la clé API pour la météo
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

def obtenir_meteo(ville: str) -> str:
    """Appelle l'API OpenWeather pour récupérer la météo d'une ville."""
    if not OPENWEATHER_API_KEY:
        return "Erreur : La clé API OpenWeather n'est pas configurée dans le backend."

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": ville,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "fr",
    }

    try:
        response = httpx.get(url, params=params, timeout=10)
        if response.status_code == 404:
            return f"Impossible de trouver la ville : {ville}."
        if response.status_code == 401:
            return "Erreur : clé API OpenWeather invalide ou pas encore activée."

        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        humidite = data["main"]["humidity"]

        return f"Météo à {ville} : {temp}°C, {description}. Humidité : {humidite}%."
    except Exception as e:
        print(f"Erreur météo : {e}")  # utile pour déboguer
        return f"Erreur temporaire lors de la récupération de la météo pour {ville}."
# Liste des outils déclarés au LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "obtenir_meteo",
            "description": "Récupère les informations météorologiques actuelles (température, description, humidité) pour une ville donnée.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ville": {
                        "type": "string",
                        "description": "Le nom de la ville (ex: Paris, Accra, Cotonou)"
                    }
                },
                "required": ["ville"]
            }
        }
    }
]

app = FastAPI(title="Study Buddy Chatbot")

from database.db import engine
import database.models as models

# Force la création de toutes les tables manquantes dans la base SQLite
models.Base.metadata.create_all(bind=engine)


class ConversationResponse(BaseModel):
    conversation_id: int


class ConversationSummary(BaseModel):
    id: int
    created_at: datetime
    preview: str | None  


class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    model: str | None = None  


class ChatResponse(BaseModel):
    reply: str
    notification: str | None = None  


class MessageResponse(BaseModel):
    seq: int
    role: str
    content: str
    created_at: datetime

class NoteRequest(BaseModel):
    content: str    


def load_messages(db: Session, conversation_id: int) -> list[Message]:
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.seq)
    ).all()


def build_llm_history(rows: list[Message]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in rows if m.role in LLM_ROLES]


@app.get("/models")
def list_models():
    return [{"id": key, "name": value} for key, value in ALLOWED_MODELS.items()]


@app.post("/conversations", status_code=201)
def create_conversation(db: Session = Depends(get_db)) -> ConversationResponse:
    conversation = Conversation()
    db.add(conversation)
    db.commit()
    return ConversationResponse(conversation_id=conversation.id)


@app.get("/conversations")
def list_conversations(db: Session = Depends(get_db)) -> list[ConversationSummary]:
    rows = db.execute(
        select(Conversation, Message.content)
        .outerjoin(Message, and_(Message.conversation_id == Conversation.id, Message.seq == 1))
        .order_by(Conversation.id.desc())
    ).all()
    return [
        ConversationSummary(
            id=conversation.id,
            created_at=conversation.created_at,
            preview=content[:PREVIEW_LENGTH] if content else None,
        )
        for conversation, content in rows
    ]


@app.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, db: Session = Depends(get_db)) -> list[MessageResponse]:
    return [
        MessageResponse(seq=m.seq, role=m.role, content=m.content, created_at=m.created_at)
        for m in load_messages(db, conversation_id)
    ]


@app.post("/conversations/{conversation_id}/notes", status_code=201)
def add_note(conversation_id: int, req: NoteRequest, db: Session = Depends(get_db)):
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    rows = load_messages(db, conversation_id)
    next_seq = rows[-1].seq + 1 if rows else 1
    
    nouvelle_note = Message(
        conversation_id=conversation_id,
        seq=next_seq,
        role=NOTE_ROLE,
        content=req.content
    )
    db.add(nouvelle_note)
    db.commit()
    
    return {"status": "Note enregistrée avec succès", "seq": next_seq}


@app.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    # 1. Déterminer et valider le modèle
    chosen_model = req.model if req.model else DEFAULT_MODEL
    if chosen_model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Modèle non autorisé par le serveur.")

    # 2. Charger l'historique depuis la base de données
    rows = load_messages(db, req.conversation_id)
    history = build_llm_history(rows)
    
    next_seq = rows[-1].seq + 1 if rows else 1
    user_message = {"role": "user", "content": req.message}
    
    # NETTOYAGE : Suppression du message systeme "charger_prompt_systeme()"
    messages = [*history, user_message]

    # 3. Premier appel au LLM en lui fournissant la liste des outils (tools)
    try:
        with httpx.Client() as client:
            response = client.post(
                RODIUMAI_URL,
                headers={"Authorization": f"Bearer {RODIUMAI_API_KEY}"},
                json={
                    "model": chosen_model,
                    "messages": messages,
                    "max_tokens": 512,
                    "tools": TOOLS,  
                },
                timeout=30,
            )
            response.raise_for_status()
            data_json = response.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Échec de connexion avec le serveur LLM.")

    # 4. Analyse de la réponse du LLM
    assistant_message = data_json["choices"][0]["message"]
    reply_text = ""

    if assistant_message.get("tool_calls"):
        messages.append(assistant_message)

        for tool_call in assistant_message["tool_calls"]:
            nom_fonction = tool_call["function"]["name"]
            try:
                arguments = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                arguments = {}

            if nom_fonction == "obtenir_meteo":
                resultat_outil = obtenir_meteo(arguments.get("ville", ""))
            else:
                resultat_outil = f"Outil inconnu : {nom_fonction}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": nom_fonction,
                "content": resultat_outil,
            })

        try:
            with httpx.Client() as client:
                second_response = client.post(
                    RODIUMAI_URL,
                    headers={"Authorization": f"Bearer {RODIUMAI_API_KEY}"},
                    json={
                        "model": chosen_model,
                        "messages": messages,
                        "max_tokens": 512,
                        "tools": TOOLS,
                    },
                    timeout=30,
                )
                second_response.raise_for_status()
                second_data = second_response.json()
                reply_text = second_data["choices"][0]["message"].get("content") or ""
        except httpx.HTTPError:
            raise HTTPException(status_code=502, detail="Échec du second appel avec le LLM.")
    else:
        reply_text = assistant_message.get("content") or ""

    # 5. Sauvegarde en base de données
    if reply_text:
        db.add_all([
            Message(conversation_id=req.conversation_id, seq=next_seq, role="user", content=req.message),
            Message(conversation_id=req.conversation_id, seq=next_seq + 1, role="assistant", content=reply_text),
        ])
        if (len(history) + 2) % NOTIFICATION_EVERY == 0:
            db.add(Message(
                conversation_id=req.conversation_id,
                seq=next_seq + 2,
                role=NOTIFICATION_ROLE,
                content=NOTIFICATION_TEXT,
            ))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Erreur de concurrence lors de la sauvegarde.")
        # 6. On renvoie une réponse JSON standard
        return {"reply": reply_text}
