# mai.py — La logique de conversation de MAI

import os
import re
from groq import Groq
from dotenv import load_dotenv
from scoring import calculer_score
from recherche_pros import rechercher_professionnels, formater_pour_chat

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Mots qui indiquent que l'utilisateur veut trouver un professionnel
MOTS_RECHERCHE = [
    "trouver", "cherche", "liste", "donne moi", "trouve",
    "m'aider à trouver", "peux tu trouver", "tu peux trouver",
    "recommande", "propose", "near", "autour", "près de",
    "dans ma zone", "dans mon secteur", "dans ma ville"
]

# Mots de localisation
MOTS_LOCALISATION = [
    "à", "sur", "pour", "à paris", "à lyon", "à marseille",
    "à bordeaux", "à lille", "à nantes", "à toulouse",
    "sur paris", "en région"
]


def detecter_demande_recherche(message: str) -> bool:
    """Détecte si l'utilisateur demande à trouver un professionnel."""
    message_lower = message.lower()
    return any(mot in message_lower for mot in MOTS_RECHERCHE)


def detecter_ville(message: str):
    """Extrait la ville mentionnée dans le message."""
    message_lower = message.lower()

    # Patterns courants : "à Paris", "sur Lyon", "pour Romainville"
    patterns = [
        r"(?:à|a|sur|pour|près de|autour de|dans)\s+([A-ZÀ-Üa-zà-ü][a-zà-ü]+(?:[-\s][A-ZÀ-Üa-zà-ü][a-zà-ü]+)*)",
        r"\b([A-ZÀ-Ü][a-zà-ü]{2,}(?:[-\s][A-ZÀ-Ü][a-zà-ü]+)*)\b"
    ]

    mots_exclus = {
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "oui", "non", "merci", "bonjour", "bonsoir", "mai", "un",
        "une", "des", "les", "vraiment", "pas", "trouver", "psychologue",
        "psychiatre", "aide", "besoin", "veux", "peux", "voudrais"
    }

    for pattern in patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        for match in matches:
            if match.lower() not in mots_exclus and len(match) > 2:
                return match

    return None


def detecter_type_pro(message: str, niveau: str) -> str:
    """Détermine le type de professionnel selon le contexte."""
    message_lower = message.lower()
    if "psychiatre" in message_lower or niveau in ["urgence", "urgence_mineur"]:
        return "psychiatre"
    elif "psychanalyste" in message_lower:
        return "psychanalyste"
    elif "thérapeute" in message_lower or "burn" in message_lower:
        return "thérapeute"
    else:
        return "psychologue"


def construire_systeme(niveau: str, age: int = 99) -> str:
    """Retourne le prompt système adapté au niveau de gravité."""

    base = """Tu es MAI (My AI), un chatbot de soutien émotionnel bienveillant.
Tu parles en français, avec un ton chaleureux et empathique.
Tu ne poses JAMAIS de diagnostic médical.
Tu ne remplaces pas un professionnel de santé.
Tu poses UNE seule question à la fois, jamais plusieurs d'un coup.
IMPORTANT : Si l'utilisateur te demande de trouver ou chercher un professionnel de santé,
dis-lui simplement "Bien sûr ! Dans quelle ville souhaites-tu que je recherche ?"
Ne dis JAMAIS que tu ne peux pas fournir de coordonnées — tu peux le faire via ta recherche intégrée.
"""

    if niveau == "soutien_leger":
        return base + """
Le niveau de détresse est faible.
Écoute avec empathie, valorise le courage de la personne,
et oriente doucement vers des activités ressourçantes ou des proches.
Reste positif et léger.
"""
    elif niveau == "orientation_pro":
        return base + """
Le niveau de détresse est modéré.
Valide le ressenti de la personne, montre que tu comprends.
Propose progressivement un suivi professionnel (psychologue, thérapeute).
Si elle ne sait pas à qui s'adresser, explique la différence entre
psychologue, psychiatre et psychanalyste simplement.
Quand l'utilisateur accepte de chercher un professionnel,
demande-lui sa ville pour lancer la recherche.
"""
    elif niveau == "urgence":
        return base + """
ATTENTION : situation potentiellement grave.
Adopte un ton très doux et rassurant.
Ne pose PAS beaucoup de questions — redirige rapidement.
Dis à la personne qu'elle n'est pas seule.
Mentionne le 3114 (numéro national prévention suicide).
Propose de l'aider à contacter un proche ou un professionnel.
Limite la conversation et oriente vers une aide humaine immédiate.
"""
    elif niveau == "urgence_mineur":
        return base + """
ATTENTION : utilisateur mineur en situation de détresse grave.
Adopte un ton ultra-doux, utilise des emojis coeur 💙.
Rappelle que des adultes de confiance peuvent aider.
Mentionne le 3114 et le 3989 (Fil Santé Jeunes).
Propose d'aider à écrire une lettre à un proche de confiance.
Ne conserve aucune donnée personnelle.
Redirige immédiatement vers un adulte ou professionnel.
"""
    return base


def chat_avec_mai(messages: list, age: int = 99) -> dict:
    """
    Envoie une conversation à MAI et retourne sa réponse.
    Détecte automatiquement les demandes de recherche de professionnels.
    """
    dernier_message = messages[-1]["content"] if messages else ""
    resultat_score = calculer_score(dernier_message, age)
    niveau = resultat_score["niveau"]

    # ── Détection automatique de recherche de professionnel ──────────────
    ville = detecter_ville(dernier_message)
    demande_recherche = detecter_demande_recherche(dernier_message)

    # Cas 1 : l'utilisateur donne une ville ET demande un professionnel
    if ville and demande_recherche:
        type_pro = detecter_type_pro(dernier_message, niveau)
        resultats = rechercher_professionnels(ville, type_pro)
        texte = formater_pour_chat(resultats, ville, type_pro)
        return {
            "reponse": texte,
            "niveau": niveau,
            "score": resultat_score["score"],
            "recherche": True,
            "resultats": resultats
        }

    # Cas 2 : l'utilisateur donne juste une ville
    # (probablement en réponse à "dans quelle ville ?")
    if ville and len(messages) >= 2:
        msg_precedent = messages[-2].get("content", "").lower()
        mots_question_ville = [
            "quelle ville", "dans quelle", "où souhaites",
            "zone", "cherche", "recherche"
        ]
        if any(mot in msg_precedent for mot in mots_question_ville):
            type_pro = detecter_type_pro(dernier_message, niveau)
            resultats = rechercher_professionnels(ville, type_pro)
            texte = formater_pour_chat(resultats, ville, type_pro)
            return {
                "reponse": texte,
                "niveau": niveau,
                "score": resultat_score["score"],
                "recherche": True,
                "resultats": resultats
            }

    # ── Conversation normale avec le LLM ─────────────────────────────────
    systeme = construire_systeme(niveau, age)
    conversation = [{"role": "system", "content": systeme}] + messages

    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        max_tokens=500,
        temperature=0.7
    )

    texte_reponse = reponse.choices[0].message.content

    return {
        "reponse": texte_reponse,
        "niveau": niveau,
        "score": resultat_score["score"],
        "recherche": False,
        "resultats": []
    }