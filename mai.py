# mai.py — Logique de conversation MAI

import os
import re
from groq import Groq
from dotenv import load_dotenv
from scoring import calculer_score
from recherche_pros import rechercher_professionnels, formater_pour_chat

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VILLES_FRANCE = {
    "paris", "marseille", "lyon", "toulouse", "nice", "nantes", "bordeaux",
    "lille", "rennes", "reims", "strasbourg", "montpellier", "grenoble",
    "dijon", "angers", "nimes", "villeurbanne", "saint-etienne", "toulon",
    "le havre", "brest", "clermont-ferrand", "limoges", "amiens", "metz",
    "besancon", "perpignan", "caen", "nancy", "argenteuil", "montreuil",
    "rouen", "mulhouse", "pau", "versailles", "colombes", "romainville",
    "vincennes", "aubervilliers", "kremlin-bicetre", "ivry", "pantin",
    "bobigny", "saint-denis", "creteil", "boulogne", "levallois", "neuilly",
    "courbevoie", "nanterre", "rueil", "vitry-sur-seine", "champigny",
    "maisons-alfort", "asnieres", "vitry", "saint-cloud", "issy",
    "clamart", "antony", "massy", "evry", "cergy", "pontoise",
    "saint-maur", "nogent", "joinville", "charenton", "alfortville",
    "choisy", "villejuif", "arcueil", "gentilly", "montrouge", "malakoff",
    "chatillon", "bagneux", "fontenay", "saint-mande", "bagnolet",
    "noisy", "bondy", "aulnay", "sevran", "tremblay", "villepinte",
    "orleans", "tours", "poitiers", "la rochelle", "bayonne", "annecy",
    "chambery", "valence", "avignon", "aix-en-provence", "cannes",
    "antibes", "menton", "monaco", "toulon"
}

MOTS_RECHERCHE = [
    "trouver un psy", "trouver un psychologue", "trouver un psychiatre",
    "trouver un psychanalyste", "trouver un thérapeute",
    "cherche un psy", "cherche un psychologue", "cherche un psychiatre",
    "donne moi une liste", "trouve moi un psy", "trouve moi un psychologue",
    "trouve moi un psychiatre", "trouve moi un thérapeute",
    "m'aider à trouver un", "orienter vers un professionnel",
    "voir un psy", "voir un psychologue", "voir un psychiatre",
    "consulter un psy", "prendre rendez-vous", "prendre rdv",
    "j'aimerais voir un", "je voudrais voir un",
    "besoin d'un psy", "besoin d'un professionnel",
    "aide moi à trouver", "trouver quelqu'un"
]

MOTS_EXCLUS_VILLE = {
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
    "oui", "non", "merci", "bonjour", "bonsoir", "mai", "salut",
    "un", "une", "des", "les", "la", "le", "mon", "ma", "mes",
    "vraiment", "pas", "trouver", "cherche", "trouve", "chercher",
    "psychologue", "psychiatre", "psychanalyste", "thérapeute", "psy",
    "aide", "besoin", "veux", "peux", "voudrais", "aimerais", "aider",
    "voir", "aller", "contacter", "appeler", "liste", "bien",
    "professionnel", "médecin", "docteur", "cabinet",
    "que", "qui", "quoi", "comment", "pourquoi", "quand", "où",
    "plus", "encore", "aussi", "donc", "alors", "après", "avant",
    "pendant", "depuis", "toujours"
}

# Mots qui signifient que la personne a déjà un suivi
MOTS_DEJA_SUIVI = [
    "j'ai déjà", "j'ai deja", "j'ai ma psy", "j'ai un psy",
    "je suis suivi", "j'ai une psy", "j'ai quelqu'un",
    "j'ai mon psy", "je vois déjà", "je consulte déjà",
    "je suis en thérapie", "j'ai mon suivi", "j'ai un thérapeute",
    "j'ai un psychiatre", "je suis accompagné", "pas besoin",
    "non merci", "c'est bon", "ça va aller", "j'ai déjà quelqu'un"
]


def analyser_conversation(messages: list, age: int) -> dict:
    score_cumule = 0
    niveau_max   = "soutien_leger"
    signaux = {
        "anxiete":          False,
        "depression":       False,
        "burnout":          False,
        "addiction":        False,
        "trauma":           False,
        "suicidaire":       False,
        "psychose":         False,
        "duree_longue":     False,
        "impact_quotidien": False,
        "deja_suivi":       False,
    }

    ordre_niveaux = {
        "soutien_leger":   0,
        "orientation_pro": 1,
        "urgence":         2,
        "urgence_mineur":  3
    }

    for msg in messages:
        if msg.get("role") != "user":
            continue

        contenu  = msg.get("content", "").lower()
        resultat = calculer_score(contenu, age)

        # Si suivi existant détecté → ne pas monter le score
        if resultat["signaux_speciaux"].get("deja_suivi"):
            signaux["deja_suivi"] = True
            continue

        score_cumule += resultat["score"]

        if ordre_niveaux.get(resultat["niveau"], 0) > ordre_niveaux.get(niveau_max, 0):
            niveau_max = resultat["niveau"]

        if age < 18 and score_cumule >= 5:
            niveau_max = "urgence_mineur"
        elif score_cumule >= 7:
            if ordre_niveaux.get(niveau_max, 0) < ordre_niveaux["urgence"]:
                niveau_max = "urgence"
        elif score_cumule >= 4:
            if ordre_niveaux.get(niveau_max, 0) < ordre_niveaux["orientation_pro"]:
                niveau_max = "orientation_pro"

        if any(m in contenu for m in ["anxieux", "anxiété", "angoisse", "panique", "stress"]):
            signaux["anxiete"] = True
        if any(m in contenu for m in ["triste", "déprimé", "vide", "seul", "pleure",
                                       "super mal", "très mal", "me sens mal", "souffre"]):
            signaux["depression"] = True
        if any(m in contenu for m in ["épuisé", "burn", "motivation", "dors mal",
                                       "fatigue", "travail", "surmenage"]):
            signaux["burnout"] = True
        if any(m in contenu for m in ["addiction", "addict", "schéma", "répète",
                                       "pornographie", "alcool", "drogue"]):
            signaux["addiction"] = True
        if any(m in contenu for m in ["trauma", "enfance", "passé", "abus", "violent"]):
            signaux["trauma"] = True
        if any(m in contenu for m in ["en finir", "mourir", "suicide", "mettre fin",
                                       "fin à ma vie", "y mettre fin", "ne plus être là"]):
            signaux["suicidaire"] = True
        if any(m in contenu for m in ["hallucin", "voix", "entend", "délire"]):
            signaux["psychose"] = True
        if any(m in contenu for m in ["depuis longtemps", "des mois", "des années",
                                       "longtemps", "ça dure"]):
            signaux["duree_longue"] = True
        if any(m in contenu for m in ["dors mal", "mange plus", "sors plus",
                                       "concentre plus", "plus de motivation"]):
            signaux["impact_quotidien"] = True

    return {"score": score_cumule, "niveau": niveau_max, "signaux": signaux}


def choisir_professionnel(signaux: dict, niveau: str, messages: list) -> str:
    for msg in reversed(messages):
        contenu = msg.get("content", "").lower()
        if "psychiatre" in contenu:   return "psychiatre"
        elif "psychanalyste" in contenu: return "psychanalyste"
        elif "thérapeute" in contenu:  return "thérapeute"
        elif "psychologue" in contenu: return "psychologue"

    if niveau in ["urgence", "urgence_mineur"] or signaux["suicidaire"] or signaux["psychose"]:
        return "psychiatre"
    if signaux["addiction"] or (signaux["trauma"] and signaux["duree_longue"]):
        return "psychanalyste"
    if signaux["burnout"] and signaux["duree_longue"]:
        return "thérapeute"
    if signaux["depression"] and signaux["duree_longue"] and signaux["impact_quotidien"]:
        return "psychiatre"
    if signaux["anxiete"] or signaux["depression"]:
        return "psychologue"
    return "psychologue"


def expliquer_choix_pro(type_pro: str, signaux: dict) -> str:
    explications = {
        "psychiatre":    "Compte tenu de ce que tu traverses, je pense qu'un psychiatre serait le plus adapté. C'est un médecin spécialisé qui peut t'écouter et t'accompagner médicalement si nécessaire.",
        "psychanalyste": "Vu ce que tu m'as partagé sur ces schémas qui se répètent, un psychanalyste serait très adapté. Il travaille en profondeur sur l'inconscient pour comprendre l'origine de ces patterns.",
        "thérapeute":    "Face à cet épuisement, un thérapeute spécialisé serait idéal. Il dispose d'outils concrets pour t'aider à retrouver de l'énergie.",
        "psychologue":   "Un psychologue serait bien adapté à ta situation. C'est un espace de parole bienveillant, pour mieux comprendre ce que tu ressens, à ton rythme.",
    }
    return explications.get(type_pro, "Un psychologue serait adapté à ta situation.")


def detecter_ville(message: str):
    message_clean = re.sub(r'[.,!?]', '', message.lower().strip())
    for ville in VILLES_FRANCE:
        if ville in message_clean:
            return ville.capitalize()
    mots = message_clean.split()
    if len(mots) <= 3:
        for mot in mots:
            if mot not in MOTS_EXCLUS_VILLE and len(mot) > 2 and mot.isalpha():
                return mot.capitalize()
    return None


def detecter_demande_recherche(message: str) -> bool:
    return any(mot in message.lower() for mot in MOTS_RECHERCHE)


def construire_systeme(niveau: str, signaux: dict, age: int = 99) -> str:
    base = """Tu es MAI (My AI), un chatbot de soutien émotionnel bienveillant.
Tu parles en français, avec un ton chaleureux, humain et empathique.
Tu tutoies toujours la personne.
Tu ne poses JAMAIS de diagnostic médical.
Tu ne remplaces pas un professionnel de santé.
Tu poses UNE seule question à la fois.

RÈGLE SUIVI EXISTANT (PRIORITAIRE) :
Si la personne dit qu'elle a DÉJÀ un psy, thérapeute, psychiatre ou suivi,
réponds avec chaleur en félicitant ce choix et demande comment tu peux
l'aider autrement. Ne propose JAMAIS de chercher un professionnel dans ce cas.
Exemple : "C'est super que tu aies déjà quelqu'un pour t'accompagner 💙
Comment puis-je t'aider autrement ?"

RÈGLE HORS SUJET (PRIORITAIRE) :
Si la conversation porte sur des sujets du quotidien (maquillage, chirurgie
esthétique, vêtements, cuisine, sport, films, voyages, mariage...),
reste dans ce registre léger et bienveillant.
Ne propose PAS de professionnel de santé sauf si la personne exprime
EXPLICITEMENT une détresse émotionnelle profonde (pleurs, dépression, etc.).

RÈGLE RECHERCHE :
Si l'utilisateur demande explicitement à trouver un professionnel,
dis : "Bien sûr ! Dans quelle ville souhaites-tu que je recherche ?"
"""

    if niveau == "soutien_leger":
        return base + "\nÉcoute avec empathie, reste positif et bienveillant.\n"

    elif niveau == "orientation_pro":
        contexte = ""
        if signaux["burnout"]:      contexte = "Épuisement professionnel possible."
        elif signaux["addiction"]:  contexte = "Schémas répétitifs ou addiction."
        elif signaux["anxiete"]:    contexte = "Anxiété présente."
        elif signaux["depression"]: contexte = "Signes de mal-être ou dépression."
        else:                       contexte = "Période difficile."

        return base + f"""
Niveau modéré. {contexte}
Valide le ressenti avec empathie.
Pose UNE question de qualification avant de proposer un professionnel.
Ne propose un professionnel QUE si la personne exprime clairement en avoir besoin.
"""

    elif niveau in ["urgence", "urgence_mineur"]:
        mineur = "MINEUR EN DÉTRESSE. " if niveau == "urgence_mineur" else ""
        jeunes = "Mentionne le 3989 (Fil Santé Jeunes)." if niveau == "urgence_mineur" else ""
        return base + f"""
{mineur}SITUATION DE CRISE GRAVE. Ton ultra-doux 💙
Valide profondément la douleur. Dis que la personne n'est pas seule.
Mentionne le 3114 (24h/24, gratuit, confidentiel). {jeunes}
NE JAMAIS demander une ville ou proposer une recherche.
NE JAMAIS dire "je ne peux pas". Phrases courtes. Beaucoup d'empathie.
"""
    return base


def chat_avec_mai(messages: list, age: int = 99) -> dict:
    dernier_message = messages[-1]["content"] if messages else ""

    analyse  = analyser_conversation(messages, age)
    niveau   = analyse["niveau"]
    signaux  = analyse["signaux"]
    type_pro = choisir_professionnel(signaux, niveau, messages)

    # ── URGENCE ───────────────────────────────────────────────────────────────
    if niveau in ["urgence", "urgence_mineur"]:
        systeme = construire_systeme(niveau, signaux, age)
        reponse = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": systeme}] + messages,
            max_tokens=400, temperature=0.5
        )
        return {
            "reponse": reponse.choices[0].message.content,
            "niveau": niveau, "score": analyse["score"],
            "recherche": False, "resultats": [], "pro_suggere": "psychiatre"
        }

    # ── Cas 1 : MAI attendait une ville ───────────────────────────────────────
    if len(messages) >= 2:
        msg_mai_precedent = ""
        for msg in reversed(messages[:-1]):
            if msg.get("role") == "assistant":
                msg_mai_precedent = msg.get("content", "").lower()
                break

        attendait_ville = any(mot in msg_mai_precedent for mot in [
            "quelle ville", "dans quelle", "souhaites-tu que je recherche",
            "quel secteur", "n'ai pas bien compris la ville"
        ])

        if attendait_ville:
            # ── La personne dit qu'elle a déjà un suivi ───────────────────────
            if any(mot in dernier_message.lower() for mot in MOTS_DEJA_SUIVI):
                systeme = construire_systeme(niveau, signaux, age)
                reponse = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": systeme}] + messages,
                    max_tokens=400, temperature=0.7
                )
                return {
                    "reponse": reponse.choices[0].message.content,
                    "niveau": niveau, "score": analyse["score"],
                    "recherche": False, "resultats": [], "pro_suggere": type_pro
                }

            # ── Extraire la ville ──────────────────────────────────────────────
            ville_brute = dernier_message.strip().rstrip(".,!?")
            for mot in ["oui", "à", "sur", "pour", "dans", "ok", "c'est", "stp", "svp", "merci"]:
                ville_brute = ville_brute.replace(mot, "").strip()

            mots          = ville_brute.split()
            est_une_ville = False

            if len(mots) <= 3:
                for ville_connue in VILLES_FRANCE:
                    if ville_connue in ville_brute.lower():
                        ville_brute   = ville_connue.capitalize()
                        est_une_ville = True
                        break
                if not est_une_ville and len(mots) == 1:
                    mot = mots[0].lower()
                    if mot not in MOTS_EXCLUS_VILLE and len(mot) > 2 and mot.isalpha():
                        est_une_ville = True

            if est_une_ville:
                resultats   = rechercher_professionnels(ville_brute, type_pro)
                explication = expliquer_choix_pro(type_pro, signaux)
                texte       = explication + "\n\n" + formater_pour_chat(resultats, ville_brute, type_pro)
                return {
                    "reponse": texte, "niveau": niveau, "score": analyse["score"],
                    "recherche": True, "resultats": resultats, "pro_suggere": type_pro
                }
            else:
                return {
                    "reponse": "Je n'ai pas bien compris la ville 😊 Dans quelle ville souhaites-tu que je recherche ? (ex : Paris, Lyon, Marseille...)",
                    "niveau": niveau, "score": analyse["score"],
                    "recherche": False, "resultats": [], "pro_suggere": type_pro
                }

    # ── Cas 2 : ville + demande dans le même message ──────────────────────────
    ville  = detecter_ville(dernier_message)
    demande = detecter_demande_recherche(dernier_message)

    if ville and demande:
        resultats   = rechercher_professionnels(ville, type_pro)
        explication = expliquer_choix_pro(type_pro, signaux)
        texte       = explication + "\n\n" + formater_pour_chat(resultats, ville, type_pro)
        return {
            "reponse": texte, "niveau": niveau, "score": analyse["score"],
            "recherche": True, "resultats": resultats, "pro_suggere": type_pro
        }

    # ── Conversation normale ──────────────────────────────────────────────────
    systeme = construire_systeme(niveau, signaux, age)
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": systeme}] + messages,
        max_tokens=500, temperature=0.7
    )

    return {
        "reponse": reponse.choices[0].message.content,
        "niveau": niveau, "score": analyse["score"],
        "recherche": False, "resultats": [], "pro_suggere": type_pro
    }