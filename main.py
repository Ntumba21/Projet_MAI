# main.py — Serveur FastAPI MAI complet

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from mai import chat_avec_mai
from database import creer_tables, get_db
from auth import (inscrire_utilisateur, connecter_utilisateur, confirmer_email,
                  creer_token, decoder_token, sauvegarder_message,
                  creer_conversation, mettre_a_jour_niveau,
                  get_historique, get_utilisateur)
from emails import envoyer_confirmation, envoyer_alerte_proche, envoyer_reset_mdp

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
creer_tables()

# Garde-fou anti-spam : emails d'alerte déjà envoyés par conversation
alertes_envoyees = set()


# ── Modèles ───────────────────────────────────────────────────────────────────

class RequeteInscription(BaseModel):
    prenom:          str
    email:           str
    mdp:             str
    age:             int
    email_proche:    Optional[str] = None
    autoriser_alerte: bool = False

class RequeteConfirmation(BaseModel):
    email: str
    code:  str

class RequeteConnexion(BaseModel):
    email: str
    mdp:   str

class RequeteChat(BaseModel):
    messages:        list
    age:             int = 99
    token:           Optional[str] = None
    conversation_id: Optional[int] = None
    latitude:        Optional[float] = None
    longitude:       Optional[float] = None
    

class RequeteResetMdp(BaseModel):
    email: str

class RequeteNouveauMdp(BaseModel):
    email:    str
    code:     str
    nouveau_mdp: str

class RequeteSuppressionCompte(BaseModel):
    token: str
    mdp:   str
    
class RequeteMajProfil(BaseModel):
    token:           str
    email_proche:    Optional[str] = None
    autoriser_alerte: bool = False
    
class RequeteCitation(BaseModel):
    texte: str
    token: str  # admin seulement




# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/inscription")
def inscription(
    req: RequeteInscription,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        print(f"Tentative inscription : {req.email}, age={req.age}")

        # Vérifier si l'email existe déjà
        from database import Utilisateur
        existant = db.query(Utilisateur).filter(
            Utilisateur.email == req.email).first()

        if existant:
            if existant.email_confirme:
                raise HTTPException(
                    status_code=400,
                    detail="Un compte existe déjà avec cet email. Connecte-toi !"
                )
            else:
                # Compte créé mais pas confirmé → renvoyer un nouveau code
                from emails import generer_code
                nouveau_code = generer_code()
                existant.code_confirmation = nouveau_code
                db.commit()
                background_tasks.add_task(
                    envoyer_confirmation,
                    existant.prenom, existant.email, nouveau_code
                )
                return {
                    "succes":  True,
                    "message": "Compte déjà créé mais pas confirmé. Nouveau code envoyé !",
                    "email":   existant.email
                }

        user, code = inscrire_utilisateur(
            db, req.prenom, req.email, req.mdp, req.age,
            req.email_proche, req.autoriser_alerte
        )
        print(f"Utilisateur créé : {user.id}")
        background_tasks.add_task(
            envoyer_confirmation, user.prenom, user.email, code
        )
        return {
            "succes":  True,
            "message": "Compte créé ! Vérifie ta boite mail.",
            "email":   user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERREUR inscription : {type(e).__name__} — {e}")
        raise HTTPException(status_code=400, detail=f"Erreur : {str(e)}")

@app.post("/confirmer-email")
def confirmer(req: RequeteConfirmation, db: Session = Depends(get_db)):
    ok = confirmer_email(db, req.email, req.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Code incorrect ou expiré.")

    from database import Utilisateur
    user = db.query(Utilisateur).filter_by(email=req.email).first()
    token = creer_token({"user_id": user.id, "email": user.email})

    # Créer une première conversation
    conv_id = creer_conversation(db, user.id)

    return {
        "succes":          True,
        "token":           token,
        "prenom":          user.prenom,
        "age":             user.age,
        "est_mineur":      user.est_mineur,
        "conversation_id": conv_id,
        "a_proche":        bool(user.email_proche),
        "alerte_active":   user.autoriser_alerte_proche
    }


@app.post("/connexion")
def connexion(req: RequeteConnexion, db: Session = Depends(get_db)):
    user = connecter_utilisateur(db, req.email, req.mdp)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    if not user.email_confirme:
        raise HTTPException(status_code=403,
                            detail="Confirme d'abord ton email avant de te connecter.")

    token   = creer_token({"user_id": user.id, "email": user.email})
    conv_id = creer_conversation(db, user.id)

    return {
        "succes":          True,
        "token":           token,
        "prenom":          user.prenom,
        "age":             user.age,
        "est_mineur":      user.est_mineur,
        "conversation_id": conv_id,
        "a_proche":        bool(user.email_proche),
        "alerte_active":   user.autoriser_alerte_proche
    }


@app.post("/nouvelle-conversation")
def nouvelle_conversation(body: dict, db: Session = Depends(get_db)):
    token = body.get("token")
    if not token:
        return {"conversation_id": None}
    payload = decoder_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    conv_id = creer_conversation(db, payload["user_id"])
    return {"conversation_id": conv_id}


@app.post("/chat")
def chat(
    req: RequeteChat,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    resultat = chat_avec_mai(req.messages, req.age)

    if req.token and req.conversation_id:
        payload = decoder_token(req.token)
        if payload:
            if req.messages:
                dernier = req.messages[-1]
                sauvegarder_message(db, req.conversation_id,
                                    dernier["role"], dernier["content"],
                                    resultat["score"])
            sauvegarder_message(db, req.conversation_id,
                                "assistant", resultat["reponse"], 0)
            mettre_a_jour_niveau(db, req.conversation_id, resultat["niveau"])

            # ── Alerte proche avec localisation ──────────────────────────────
            cle_alerte = f"{payload['user_id']}_{req.conversation_id}"
            if (resultat["niveau"] in ["urgence", "urgence_mineur"]
                    and resultat.get("pro_suggere") == "psychiatre"
                    and cle_alerte not in alertes_envoyees):

                user = get_utilisateur(db, payload["user_id"])
                if user and user.email_proche and user.autoriser_alerte_proche:
                    alertes_envoyees.add(cle_alerte)
                    background_tasks.add_task(
                        envoyer_alerte_proche,
                        user.prenom,
                        user.email_proche,
                        req.latitude,   
                        req.longitude
                    )

    return resultat


@app.get("/historique")
def historique(token: str, db: Session = Depends(get_db)):
    payload = decoder_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    return {"historique": get_historique(db, payload["user_id"])}



@app.get("/dashboard")
def dashboard(token: str, db: Session = Depends(get_db)):
    payload = decoder_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")

    from database import Conversation, Message
    from collections import Counter
    import re

    # Récupérer tous les messages utilisateur des 30 derniers jours
    from datetime import datetime, timedelta
    date_limite = datetime.utcnow() - timedelta(days=30)

    convs = (db.query(Conversation)
               .filter(Conversation.utilisateur_id == payload["user_id"])
               .filter(Conversation.date_debut >= date_limite)
               .all())

    tous_messages_user = []
    niveaux            = []
    scores             = []

    for conv in convs:
        niveaux.append(conv.niveau_max)
        msgs = (db.query(Message)
                  .filter(Message.conversation_id == conv.id)
                  .filter(Message.role == "user")
                  .all())
        for msg in msgs:
            tous_messages_user.append(msg.contenu.lower())
            scores.append(msg.score)

    # Analyse des thèmes abordés
    themes = {
        "Anxiété / Stress":      ["anxieux", "anxiété", "stress", "angoisse", "panique"],
        "Tristesse / Dépression": ["triste", "déprimé", "vide", "pleure", "malheureux"],
        "Travail / Burn-out":    ["travail", "boulot", "épuisé", "burn-out", "motivation"],
        "Relations":             ["famille", "ami", "couple", "seul", "isolé"],
        "Sommeil":               ["dors mal", "insomnie", "fatigue", "réveil"],
        "Addiction":             ["addiction", "alcool", "drogue", "arrêter"],
        "Identité / Sens":       ["qui suis-je", "sens", "identité", "avenir", "perdu"],
    }

    scores_themes = {}
    for theme, mots in themes.items():
        count = sum(
            1 for msg in tous_messages_user
            if any(mot in msg for mot in mots)
        )
        if count > 0:
            scores_themes[theme] = count

    # Trier par fréquence
    themes_tries = sorted(scores_themes.items(), key=lambda x: x[1], reverse=True)

    # Niveau global
    ordre = {"soutien_leger": 0, "orientation_pro": 1,
             "urgence": 2, "urgence_mineur": 3}
    niveau_global = max(niveaux, key=lambda n: ordre.get(n, 0)) if niveaux else "soutien_leger"

    # Score moyen
    score_moyen = round(sum(scores) / len(scores), 1) if scores else 0

    # Évolution sur 7 jours
    evolution = []
    for i in range(6, -1, -1):
        date_j = datetime.utcnow() - timedelta(days=i)
        convs_j = [c for c in convs
                   if c.date_debut.date() == date_j.date()]
        score_j = 0
        if convs_j:
            msgs_j = []
            for conv in convs_j:
                msgs_j += db.query(Message).filter(
                    Message.conversation_id == conv.id,
                    Message.role == "user"
                ).all()
            if msgs_j:
                score_j = round(sum(m.score for m in msgs_j) / len(msgs_j), 1)
        evolution.append({
            "jour":  date_j.strftime("%d/%m"),
            "score": score_j
        })

    return {
        "nb_conversations":  len(convs),
        "niveau_global":     niveau_global,
        "score_moyen":       score_moyen,
        "themes":            [{"theme": t, "count": c} for t, c in themes_tries[:5]],
        "evolution":         evolution,
    }


@app.get("/")
def accueil():
    return {"message": "MAI est en ligne 👋"}


@app.post("/mot-de-passe-oublie")
def mot_de_passe_oublie(
    req: RequeteResetMdp,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from database import Utilisateur
    from emails import generer_code
    user = db.query(Utilisateur).filter(Utilisateur.email == req.email).first()
    if not user:
        # On ne révèle pas si l'email existe ou non (sécurité)
        return {"succes": True, "message": "Si cet email existe, un code a été envoyé."}

    code = generer_code()
    user.code_confirmation = code
    db.commit()

    background_tasks.add_task(envoyer_reset_mdp, user.prenom, user.email, code)
    return {"succes": True, "message": "Code envoyé par email."}


@app.post("/reinitialiser-mdp")
def reinitialiser_mdp(req: RequeteNouveauMdp, db: Session = Depends(get_db)):
    from database import Utilisateur
    from auth import hasher_mdp
    user = db.query(Utilisateur).filter(Utilisateur.email == req.email).first()
    if not user or user.code_confirmation != req.code:
        raise HTTPException(status_code=400, detail="Code incorrect ou expiré.")
    if len(req.nouveau_mdp) < 6:
        raise HTTPException(status_code=400, detail="Mot de passe trop court.")
    user.mot_de_passe    = hasher_mdp(req.nouveau_mdp)
    user.code_confirmation = None
    db.commit()
    return {"succes": True, "message": "Mot de passe mis à jour !"}


@app.delete("/supprimer-compte")
def supprimer_compte(req: RequeteSuppressionCompte, db: Session = Depends(get_db)):
    from database import Utilisateur
    from auth import verifier_mdp
    payload = decoder_token(req.token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    user = db.query(Utilisateur).filter(
        Utilisateur.id == payload["user_id"]).first()
    if not user or not verifier_mdp(req.mdp, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect.")
    db.delete(user)
    db.commit()
    return {"succes": True, "message": "Compte supprimé."}

@app.put("/profil")
def maj_profil(req: RequeteMajProfil, db: Session = Depends(get_db)):
    payload = decoder_token(req.token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    from database import Utilisateur
    user = db.query(Utilisateur).filter(
        Utilisateur.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user.email_proche            = req.email_proche
    user.autoriser_alerte_proche = req.autoriser_alerte
    db.commit()
    return {"succes": True, "message": "Profil mis à jour !"}

@app.get("/profil")
def get_profil(token: str, db: Session = Depends(get_db)):
    payload = decoder_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    from database import Utilisateur
    user = db.query(Utilisateur).filter(
        Utilisateur.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return {
        "prenom":          user.prenom,
        "email":           user.email,
        "age":             user.age,
        "email_proche":    user.email_proche,
        "alerte_active":   user.autoriser_alerte_proche
    }

@app.get("/citations")
def get_citations(db: Session = Depends(get_db)):
    """Retourne toutes les citations actives (aléatoire)."""
    from database import Citation
    import random
    citations = db.query(Citation).filter(Citation.actif == True).all()
    if not citations:
        return {"citations": CITATIONS_DEFAUT}
    random.shuffle(citations)
    return {"citations": [c.texte for c in citations]}

@app.post("/citations")
def ajouter_citation(req: RequeteCitation, db: Session = Depends(get_db)):
    """Ajouter une citation (authentifié)."""
    payload = decoder_token(req.token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    from database import Citation
    citation = Citation(texte=req.texte.strip())
    db.add(citation)
    db.commit()
    return {"succes": True, "message": "Citation ajoutée !"}

@app.delete("/citations/{citation_id}")
def supprimer_citation(citation_id: int, token: str, db: Session = Depends(get_db)):
    """Désactiver une citation."""
    payload = decoder_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide.")
    from database import Citation
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation introuvable.")
    citation.actif = False
    db.commit()
    return {"succes": True}

# Citations par défaut si la base est vide
CITATIONS_DEFAUT = [
    "Chaque jour est une nouvelle chance de te sentir mieux. 💙",
    "Tu n'as pas à tout régler aujourd'hui. Un pas à la fois. 🌱",
    "Tes émotions sont valides. Prends soin de toi. 🤍",
    "La vulnérabilité est une force, pas une faiblesse. ✨",
    "Tu mérites d'être écouté(e) et compris(e). 💛",
    "Respire. Ce moment passera. 🌊",
    "Demander de l'aide est un acte de courage. 🦋",
    "Tu n'es pas seul(e). Des gens tiennent à toi. 💜",
    "Chaque petit progrès compte. 🌟",
    "Prendre soin de sa santé mentale, c'est prendre soin de soi. 🌸",
    "Tu as déjà surmonté des choses difficiles. 💪",
    "La guérison n'est pas linéaire, et c'est normal. 🌈",
]
