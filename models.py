from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# parte 2
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), default="Nueva conversación")
    created_at = Column(DateTime, default=lambda:  datetime.now(timezone.utc))

    owner = relationship("User", back_populates="conversations")

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

# paso 3
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    

    conversation = relationship("Conversation", back_populates="messages")


# Parte 6 
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # (Unique Key): no permite dos usuarios con el mismo nombre
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")
