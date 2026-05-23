# scoring.py — Algorithme de décision MAI

MOTS_URGENCE = [
    "mourir", "suicide", "me tuer", "plus envie de vivre",
    "fin à ma vie", "disparaître", "je veux mourir",
    "envie de mourir", "mettre fin à mes jours",
    "plus envie d'être là", "en finir", "y mettre fin",
    "j'en peux plus de vivre", "tout arrêter définitivement",
    "ne plus être là", "mettre fin à tout"
]

MOTS_ANXIETE = [
    "anxieux", "anxiété", "angoisse", "stressé", "stress", "panique",
    "inquiet", "terrifié", "oppressé", "sous pression", "j'angoisse"
]

MOTS_TRISTESSE = [
    "triste", "déprimé", "vide", "malheureux", "dépression",
    "épuisé", "épuisement", "burn-out", "burnout",
    "je me sens mal", "me sens mal", "je vais pas bien",
    "ça ne va pas", "je ne vais pas bien", "mal dans ma tête",
    "super mal", "très mal", "je souffre",
    "plus de motivation", "plus envie", "plus d'énergie",
    "dors mal", "je dors mal", "insomnies", "je pleure",
    "seul", "isolé", "personne ne comprend"
]

MOTS_CONSULTATION = [
    "consulter", "consulte", "voir un psy", "voir un professionnel",
    "prendre rdv", "prendre rendez-vous",
    "besoin d'aide", "j'ai besoin d'aide",
    "cherche de l'aide", "soutien psychologique",
    "thérapie", "j'aimerais consulter"
]

MOTS_DUREE_LONGUE = [
    "depuis des semaines", "depuis des mois", "depuis longtemps",
    "ça dure", "depuis un moment", "depuis un an", "depuis toujours",
    "depuis des années", "ça fait longtemps"
]

MOTS_IMPACT = [
    "je dors mal", "plus de motivation", "je mange plus",
    "je sors plus", "je me concentre plus", "j'arrive plus",
    "plus de plaisir", "rien ne m'intéresse"
]

MOTS_SCHEMA_REPETITIF = [
    "ça se répète", "toujours pareil", "schéma", "encore et encore",
    "je recommence", "je retombe", "addiction", "addict",
    "j'arrive pas à arrêter", "pornographie", "alcool", "drogue"
]

MOTS_TRAUMA = [
    "trauma", "traumatisme", "enfance difficile", "abus",
    "violence", "agression", "choc", "depuis petit"
]

MOTS_PSYCHOSE = [
    "j'entends des voix", "je vois des choses", "hallucination",
    "on me surveille", "on me suit", "complot", "persécuté"
]

# ── Mots qui indiquent que la personne a DÉJÀ un suivi ───────────────────────
MOTS_DEJA_SUIVI = [
    "j'ai déjà", "j'ai deja", "j'ai ma psy", "j'ai un psy",
    "je suis suivi", "j'ai une psy", "j'ai quelqu'un",
    "j'ai mon psy", "je vois déjà", "je consulte déjà",
    "je suis en thérapie", "j'ai mon suivi", "j'ai un thérapeute",
    "j'ai un psychiatre", "je suis accompagné", "j'ai déjà quelqu'un"
]

# ── Contextes du quotidien qui ne sont PAS de la détresse psy ────────────────
CONTEXTES_QUOTIDIEN = [
    "maquillage", "chirurgie esthétique", "botox", "filler",
    "coiffure", "look", "tenue", "vêtement", "robe",
    "mariage", "fête", "soirée", "anniversaire",
    "recette", "cuisine", "sport", "match", "film", "série",
    "voyage", "vacances", "voiture", "travaux", "appartement",
    "shopping", "chaussures", "sac", "parfum"
]

# Mots de détresse qui réactivent le scoring même dans un contexte quotidien
MOTS_DETRESSE_FORTE = [
    "je souffre", "je pleure", "je vais très mal", "déprimé",
    "anxieux", "suicid", "mourir", "en finir", "je n'en peux plus"
]


def calculer_score(message: str, age: int = 99) -> dict:
    message_lower = message.lower()
    score = 0
    details = []
    signaux_speciaux = {
        "schema_repetitif": False,
        "trauma":           False,
        "psychose":         False,
        "deja_suivi":       False,
    }

    # ── Détecter si la personne a déjà un suivi ──────────────────────────────
    for mot in MOTS_DEJA_SUIVI:
        if mot in message_lower:
            signaux_speciaux["deja_suivi"] = True
            details.append(f"✅ Suivi existant détecté : '{mot}'")
            return {
                "score":            0,
                "niveau":           "soutien_leger",
                "details":          details,
                "signaux_speciaux": signaux_speciaux
            }

    # ── Contexte quotidien sans détresse → score 0 ───────────────────────────
    for contexte in CONTEXTES_QUOTIDIEN:
        if contexte in message_lower:
            detresse_presente = any(m in message_lower for m in MOTS_DETRESSE_FORTE)
            if not detresse_presente:
                return {
                    "score":   0,
                    "niveau":  "soutien_leger",
                    "details": [f"Contexte quotidien : '{contexte}'"],
                    "signaux_speciaux": signaux_speciaux
                }

    # ── Urgence (+5) ─────────────────────────────────────────────────────────
    for mot in MOTS_URGENCE:
        if mot in message_lower:
            score += 5
            details.append(f"🚨 Urgence : '{mot}'")
            break

    # ── Anxiété (+2) ─────────────────────────────────────────────────────────
    for mot in MOTS_ANXIETE:
        if mot in message_lower:
            score += 2
            details.append("😰 Anxiété")
            break

    # ── Tristesse/mal-être (+3) ───────────────────────────────────────────────
    for mot in MOTS_TRISTESSE:
        if mot in message_lower:
            score += 3
            details.append(f"😔 Mal-être : '{mot}'")
            break

    # ── Consultation (+2) ────────────────────────────────────────────────────
    for mot in MOTS_CONSULTATION:
        if mot in message_lower:
            score += 2
            details.append(f"🤝 Demande aide : '{mot}'")
            break

    # ── Durée longue (+2) ────────────────────────────────────────────────────
    for mot in MOTS_DUREE_LONGUE:
        if mot in message_lower:
            score += 2
            details.append("⏳ Durée longue")
            break

    # ── Impact quotidien (+2) ────────────────────────────────────────────────
    for mot in MOTS_IMPACT:
        if mot in message_lower:
            score += 2
            details.append("📉 Impact quotidien")
            break

    # ── Signaux spéciaux ─────────────────────────────────────────────────────
    for mot in MOTS_SCHEMA_REPETITIF:
        if mot in message_lower:
            signaux_speciaux["schema_repetitif"] = True
            break

    for mot in MOTS_TRAUMA:
        if mot in message_lower:
            signaux_speciaux["trauma"] = True
            break

    for mot in MOTS_PSYCHOSE:
        if mot in message_lower:
            signaux_speciaux["psychose"] = True
            score += 5
            details.append("🧠 Signal psychose")
            break

    # ── Niveau ───────────────────────────────────────────────────────────────
    if age < 18 and score >= 5:
        niveau = "urgence_mineur"
    elif score >= 7:
        niveau = "urgence"
    elif score >= 4:
        niveau = "orientation_pro"
    else:
        niveau = "soutien_leger"

    return {
        "score":            score,
        "niveau":           niveau,
        "details":          details,
        "signaux_speciaux": signaux_speciaux
    }