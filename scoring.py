# scoring.py — L'algorithme de décision de MAI

# Mots-clés qui indiquent une situation d'urgence
MOTS_URGENCE = [
    "mourir", "en finir", "suicide", "me tuer", "plus envie de vivre",
    "mettre fin", "fin à ma vie", "disparaître", "je veux mourir"
]

# Mots-clés qui indiquent de l'anxiété ou de la tristesse
MOTS_ANXIETE = [
    "anxieux", "anxiété", "angoisse", "stressé", "panique",
    "inquiet", "peur", "terrifié"
]

MOTS_TRISTESSE = [
    "triste", "déprimé", "vide", "seul", "épuisé", "plus de motivation",
    "dors mal", "pleure", "malheureux", "burn-out", "burnout"
]

# Mots-clés qui indiquent une durée longue
MOTS_DUREE_LONGUE = [
    "depuis des semaines", "depuis des mois", "depuis longtemps",
    "ça dure", "depuis un moment", "depuis un an"
]

# Mots-clés qui indiquent un impact sur le quotidien
MOTS_IMPACT = [
    "je dors mal", "plus de motivation", "je travaille plus",
    "je mange plus", "je sors plus", "je pleure tout le temps"
]


def calculer_score(message: str, age: int = 99) -> dict:
    """
    Calcule le score de gravité d'un message.
    Retourne le score et le niveau d'intervention.
    """
    message_lower = message.lower()
    score = 0
    details = []

    # Vérifier les mots d'urgence (+5 si trouvé)
    for mot in MOTS_URGENCE:
        if mot in message_lower:
            score += 5
            details.append(f"Urgence détectée : '{mot}'")
            break  # un seul suffit

    # Vérifier l'anxiété (+2)
    for mot in MOTS_ANXIETE:
        if mot in message_lower:
            score += 2
            details.append("Anxiété détectée")
            break

    # Vérifier la tristesse/épuisement (+3)
    for mot in MOTS_TRISTESSE:
        if mot in message_lower:
            score += 3
            details.append("Tristesse/épuisement détecté")
            break

    # Vérifier la durée longue (+2)
    for mot in MOTS_DUREE_LONGUE:
        if mot in message_lower:
            score += 2
            details.append("Durée longue détectée")
            break

    # Vérifier l'impact quotidien (+2)
    for mot in MOTS_IMPACT:
        if mot in message_lower:
            score += 2
            details.append("Impact quotidien détecté")
            break

    # Déterminer le niveau d'intervention
    if age < 18 and score >= 5:
        niveau = "urgence_mineur"
    elif score >= 7:
        niveau = "urgence"
    elif score >= 4:
        niveau = "orientation_pro"
    else:
        niveau = "soutien_leger"

    return {
        "score": score,
        "niveau": niveau,
        "details": details
    }