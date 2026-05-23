# auth.py — Authentification MAI

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Utilisateur
from emails import generer_code
import os

SECRET_KEY  = os.getenv("SECRET_KEY", "mai-secret-key-2024")
ALGORITHM   = "HS256"
EXPIRATION  = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hasher_mdp(mdp: str) -> str:
    return pwd_context.hash(mdp)

def verifier_mdp(mdp: str, hash: str) -> bool:
    return pwd_context.verify(mdp, hash)

def creer_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=EXPIRATION)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decoder_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def inscrire_utilisateur(
    db: Session, prenom: str, email: str, mdp: str, age: int,
    email_proche: str = None, autoriser_alerte: bool = False
) -> Utilisateur:
    code = generer_code()
    utilisateur = Utilisateur(
        prenom                  = prenom,
        email                   = email,
        mot_de_passe            = hasher_mdp(mdp),
        age                     = age,
        est_mineur              = age < 18,
        email_confirme          = False,
        code_confirmation       = code,
        email_proche            = email_proche,
        autoriser_alerte_proche = autoriser_alerte
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur, code


def confirmer_email(db: Session, email: str, code: str) -> bool:
    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if not user or user.code_confirmation != code:
        return False
    user.email_confirme    = True
    user.code_confirmation = None
    db.commit()
    return True


def connecter_utilisateur(db: Session, email: str, mdp: str) -> Utilisateur | None:
    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if not user or not verifier_mdp(mdp, user.mot_de_passe):
        return None
    return user


def sauvegarder_message(db: Session, conversation_id: int,
                         role: str, contenu: str, score: int = 0):
    from database import Message
    msg = Message(
        conversation_id = conversation_id,
        role            = role,
        contenu         = contenu,
        score           = score
    )
    db.add(msg)
    db.commit()


def creer_conversation(db: Session, utilisateur_id: int) -> int:
    from database import Conversation
    conv = Conversation(utilisateur_id=utilisateur_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv.id


def mettre_a_jour_niveau(db: Session, conversation_id: int, niveau: str):
    from database import Conversation
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id).first()
    if conv:
        conv.niveau_max = niveau
        db.commit()


def get_historique(db: Session, utilisateur_id: int) -> list:
    from database import Conversation, Message
    convs = (db.query(Conversation)
               .filter(Conversation.utilisateur_id == utilisateur_id)
               .order_by(Conversation.date_debut.desc())
               .limit(20).all())
    historique = []
    for conv in convs:
        msgs = (db.query(Message)
                  .filter(Message.conversation_id == conv.id)
                  .order_by(Message.horodatage).all())
        historique.append({
            "id":          conv.id,
            "date":        conv.date_debut.strftime("%d/%m/%Y %H:%M"),
            "niveau_max":  conv.niveau_max,
            "nb_messages": len(msgs),
            "apercu":      msgs[0].contenu[:60] + "..." if msgs else "Conversation vide",
            "messages":    [{"role": m.role, "contenu": m.contenu,
                             "heure": m.horodatage.strftime("%H:%M")}
                            for m in msgs]
        })
    return historique


def get_utilisateur(db: Session, user_id: int) -> Utilisateur | None:
    return db.query(Utilisateur).filter(Utilisateur.id == user_id).first()