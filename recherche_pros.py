# recherche_pros.py — Recherche de professionnels de santé mentale par ville

import os
import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")

# Types de professionnels selon le niveau de MAI
TYPES_PRO = {
    "psychologue":    "psychologue",
    "psychiatre":     "psychiatre",
    "psychanalyste":  "psychanalyste",
    "therapiste":     "thérapeute",
}


def rechercher_professionnels(ville: str, type_pro: str = "psychologue") -> list:
    """
    Recherche des professionnels de santé mentale dans une ville.
    Retourne une liste de résultats formatés.
    """
    if not GOOGLE_KEY:
        return resultats_fictifs(ville, type_pro)

    try:
        # Appel à l'API Google Places
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{type_pro} santé mentale {ville} France",
            "language": "fr",
            "key": GOOGLE_KEY,
            "type": "doctor"
        }

        reponse = requests.get(url, params=params, timeout=5)
        data = reponse.json()

        if data.get("status") != "OK" or not data.get("results"):
            return resultats_fictifs(ville, type_pro)

        # Formater les résultats
        resultats = []
        for lieu in data["results"][:5]:  # max 5 résultats
            note = lieu.get("rating", None)
            adresse = lieu.get("formatted_address", "Adresse non disponible")
            # Simplifier l'adresse (enlever ", France")
            adresse = adresse.replace(", France", "")

            resultats.append({
                "nom":     lieu.get("name", "Professionnel"),
                "adresse": adresse,
                "note":    f"⭐ {note}/5" if note else "Note non disponible",
                "ouvert":  "🟢 Ouvert" if lieu.get("opening_hours", {}).get("open_now") else "Horaires non renseignés"
            })

        return resultats if resultats else resultats_fictifs(ville, type_pro)

    except Exception:
        return resultats_fictifs(ville, type_pro)


def resultats_fictifs(ville: str, type_pro: str) -> list:
    """
    Retourne des résultats fictifs si l'API n'est pas disponible.
    Utile pour les démonstrations sans clé API.
    """
    return [
        {
            "nom":     f"Cabinet {type_pro.capitalize()} Centre",
            "adresse": f"12 rue de la Paix, {ville}",
            "note":    "⭐ 4.5/5",
            "ouvert":  "🟢 Ouvert"
        },
        {
            "nom":     f"Dr. Martin — {type_pro.capitalize()}",
            "adresse": f"8 avenue des Lilas, {ville}",
            "note":    "⭐ 4.8/5",
            "ouvert":  "Horaires non renseignés"
        },
        {
            "nom":     f"Espace Bien-Être {ville}",
            "adresse": f"3 boulevard Voltaire, {ville}",
            "note":    "⭐ 4.2/5",
            "ouvert":  "🟢 Ouvert"
        },
    ]


def formater_pour_chat(resultats: list, ville: str, type_pro: str) -> str:
    """
    Formate les résultats en texte lisible pour la conversation MAI.
    """
    if not resultats:
        return f"Je n'ai pas trouvé de {type_pro} à {ville}. Essaie une ville voisine."

    texte = f"Voici ce que j'ai trouvé comme {type_pro} à {ville} :\n\n"

    for i, pro in enumerate(resultats, 1):
        texte += f"{i}. {pro['nom']}\n"
        texte += f"   📍 {pro['adresse']}\n"
        texte += f"   {pro['note']} · {pro['ouvert']}\n\n"

    texte += "Tu peux les appeler pour prendre rendez-vous. Souhaites-tu autre chose ?"
    return texte