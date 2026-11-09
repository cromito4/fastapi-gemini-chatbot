from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import engine, Base, get_db
import models
from auth import hash_password, verify_password, create_access_token, get_current_user
from gemini_service import get_gemini_response

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot con Gemini API")

# Datos que solicita pydantic

class UserRegisterRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class CreateConversationRequest(BaseModel):
    title: str = "Nueva conversación"

class ChatRequest(BaseModel):
    conversation_id: int
    message: str


# ENDPOINT: Interfaz Interactiva de Scalar

@app.get("/scalar", response_class=HTMLResponse, include_in_schema=False)
async def scalar_html():
    return f"""
    <!doctype html>
    <html>
      <head>
        <title>{app.title} - Scalar</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <script
          id="api-reference"
          data-url="{app.openapi_url}"
        ></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """


# ==========================================================
# ENDPOINT 1: REGISTRO DE CUENTA NUEVA (POST /register)
# ==========================================================
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
# Revisar si el nombre de usuario ya está registrado
    existing_user = db.query(models.User).filter(models.User.username == req.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
# Pasar la contraseña por la trituradora
    hashed_pwd = hash_password(req.password)
# Crear el nuevo usuario con la contraseña ya triturada
    new_user = models.User(username=req.username, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuario registrado exitosamente", "user_id": new_user.id}


# ==========================================================
# ENDPOINT 2: INICIO DE SESIÓN / LOGIN (POST /login)
# ==========================================================
@app.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
# Buscar al usuario por su nombre de usuario
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
# Verificar si no existe O si la contraseña escrita no coincide
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
# Fabricar el Token JWT
    token = create_access_token(data={"user_id": user.id, "sub": user.username})

    return {"access_token": token, "token_type": "bearer"}


# ==========================================================
# ENDPOINT 3: CREAR CONVERSACIÓN (POST /conversations)
# ==========================================================
@app.post("/conversations")
def create_conversation(
    req: CreateConversationRequest,
    current_user: models.User = Depends(get_current_user),  # El guardia verifica el Token y nos da al usuario logueado
    db: Session = Depends(get_db)
):
    # Creamos la conversación vinculándola al ID del usuario logueado
    new_conv = models.Conversation(title=req.title, user_id=current_user.id)
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)

    return {
        "id": new_conv.id,
        "title": new_conv.title,
        "user_id": new_conv.user_id,
        "message": "Conversación creada exitosamente"
    }


# ==========================================================
# ENDPOINT 4: VER TODOS MIS CHATS (GET /conversations)
# ==========================================================
@app.get("/conversations")
def get_my_conversations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
# Buscar únicamente los chats que le pertenecen a "x" usuario
    my_convs = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).all()
# la lista ordenada de sus conversaciones
    return [
        {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at
        }
        for conv in my_convs
    ]


# ==========================================================
# ENDPOINT 5: VER HISTORIAL DE UN CHAT (GET /conversations/{conversation_id}/messages)
# ==========================================================
@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
# Verificar que la conversación exista Y que sea del usuario logueado
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=404,
            detail="La conversación no existe o no tienes permiso para verla"
        )
# Traer todos los mensajes de ese chat ordenados por su fecha
    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conv.id
    ).order_by(models.Message.created_at.asc()).all()
# la lista de mensajes
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in messages
    ]


# ==========================================================
# ENDPOINT 6: BORRAR UN CHAT (DELETE /conversations/{conversation_id})
# ==========================================================
@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
# Verificar que la conversación exista Y que sea del usuario logueado
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=404,
            detail="La conversación no existe o no tienes permiso para borrarla"
        )
# Borrar la conversación
    db.delete(conv)
    db.commit()
# Devolver confirmación
    return {"message": f"Conversación {conversation_id} eliminada exitosamente"}

    
# ==========================================================
# ENDPOINT 7: CHATEAR CON GEMINI (POST /chat)
# ==========================================================
@app.post("/chat")
def chat(
    req: ChatRequest,
    current_user: models.User = Depends(get_current_user),  # El guardia verifica que el usuario esté autenticado
    db: Session = Depends(get_db)
):
    # Verificar que la conversación exista Y que le pertenezca al usuario logueado
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == req.conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="La conversación no existe o no tienes permiso para chatear en ella")

    # Guardar el mensaje que acaba de enviar el usuario
    user_msg = models.Message(
        conversation_id=conv.id,
        role="user",
        content=req.message
    )
    db.add(user_msg)
    db.commit()

    # Obtener todos los mensajes de esta conversación ordenados cronológicamente
    history = db.query(models.Message).filter(
        models.Message.conversation_id == conv.id
    ).order_by(models.Message.created_at.asc()).all()

    # Preguntarle a Gemini teniendo en cuenta todo el historial acumulado
    bot_reply_text = get_gemini_response(history)
    
    # Guardar la respuesta generada por Gemini en la base de datos
    bot_msg = models.Message(
        conversation_id=conv.id,
        role="model",
        content=bot_reply_text
    )
    db.add(bot_msg)
    db.commit()

    # Devolver la respuesta al usuario
    return {
        "conversation_id": conv.id,
        "reply": bot_reply_text
    }
