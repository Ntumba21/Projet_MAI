# main.py — Le serveur FastAPI de MAI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mai import chat_avec_mai

app = FastAPI()

# Autoriser les connexions depuis n'importe quelle origine
# (nécessaire pour que l'interface web puisse parler au serveur)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structure d'une requête envoyée au serveur
class RequeteChat(BaseModel):
    messages: list   # toute la conversation
    age: int = 99    # âge de l'utilisateur (99 = non renseigné)


@app.get("/")
def accueil():
    return {"message": "MAI est en ligne 👋"}


@app.post("/chat")
def chat(requete: RequeteChat):
    """
    Point d'entrée principal.
    Reçoit la conversation, retourne la réponse de MAI.
    """
    resultat = chat_avec_mai(requete.messages, requete.age)
    return resultat