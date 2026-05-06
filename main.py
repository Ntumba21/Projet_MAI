# main.py — Le serveur FastAPI de MAI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mai import chat_avec_mai
from recherche_pros import rechercher_professionnels, formater_pour_chat


    
    
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
    resultat = chat_avec_mai(requete.messages, requete.age)
    return resultat

class RequeteRecherche(BaseModel):
    ville: str
    type_pro: str = "psychologue"

@app.post("/recherche")
def recherche(requete: RequeteRecherche):
    """
    Recherche des professionnels de santé mentale dans une ville.
    """
    resultats = rechercher_professionnels(requete.ville, requete.type_pro)
    texte = formater_pour_chat(resultats, requete.ville, requete.type_pro)
    return {
        "resultats": resultats,
        "texte": texte
    }
    
