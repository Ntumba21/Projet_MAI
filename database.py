# database.py — Configuration PostgreSQL

from sqlalchemy import (create_engine, Column, Integer, String,
                        Text, DateTime, Boolean, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/mai_db"
)

engine       = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base         = declarative_base()


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id                      = Column(Integer, primary_key=True, index=True)
    prenom                  = Column(String(50), nullable=False)
    email                   = Column(String(100), unique=True, index=True, nullable=False)
    mot_de_passe            = Column(String(200), nullable=False)
    age                     = Column(Integer, nullable=False)
    est_mineur              = Column(Boolean, default=False)
    date_creation           = Column(DateTime, default=datetime.utcnow)

    # Email confirmé
    email_confirme          = Column(Boolean, default=False)
    code_confirmation       = Column(String(6), nullable=True)

    # Proche de confiance
    email_proche            = Column(String(100), nullable=True)
    autoriser_alerte_proche = Column(Boolean, default=False)

    conversations = relationship("Conversation", back_populates="utilisateur",
                                 cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id             = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    date_debut     = Column(DateTime, default=datetime.utcnow)
    niveau_max     = Column(String(30), default="soutien_leger")
    resume         = Column(Text, nullable=True)

    utilisateur = relationship("Utilisateur", back_populates="conversations")
    messages    = relationship("Message", back_populates="conversation",
                               cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id              = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role            = Column(String(10), nullable=False)
    contenu         = Column(Text, nullable=False)
    horodatage      = Column(DateTime, default=datetime.utcnow)
    score           = Column(Integer, default=0)

    conversation = relationship("Conversation", back_populates="messages")
    
class Citation(Base):
    __tablename__ = "citations"

    id        = Column(Integer, primary_key=True, index=True)
    texte     = Column(Text, nullable=False)
    actif     = Column(Boolean, default=True)
    date_ajout = Column(DateTime, default=datetime.utcnow)


def creer_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()