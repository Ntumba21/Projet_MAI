# recherche_pros.py — Redirection intelligente vers Doctolib

TYPES_DOCTOLIB = {
    "psychologue":   "psychologue",
    "psychiatre":    "psychiatre",
    "psychanalyste": "psychanalyste",
    "thérapeute":    "psychotherapeute",
}


def rechercher_professionnels(ville: str, type_pro: str = "psychologue") -> list:
    """
    Génère des liens directs vers Doctolib, Mondocteur et l'Ordre des Psychologues.
    Simple, fiable, et c'est exactement ce que font les vraies applis de santé.
    """
    ville_slug = (ville.lower().strip()
                  .replace(" ", "-")
                  .replace("é", "e")
                  .replace("è", "e")
                  .replace("ê", "e")
                  .replace("à", "a")
                  .replace("â", "a")
                  .replace("î", "i")
                  .replace("ô", "o")
                  .replace("û", "u")
                  .replace("ç", "c"))
    type_slug = TYPES_DOCTOLIB.get(type_pro, "psychologue")
    ville_aff = ville.strip().capitalize()

    return [
        {
            "nom":     f"Doctolib — {type_pro.capitalize()}s à {ville_aff}",
            "adresse": f"Résultats filtrés : {type_pro} + {ville_aff} + disponibilités",
            "note":    "📞 Prise de RDV en ligne 24h/24",
            "ouvert":  "🌐 doctolib.fr",
            "lien":    f"https://www.doctolib.fr/{type_slug}/{ville_slug}"
        },
        {
            "nom":     f"Mondocteur — {type_pro.capitalize()}s à {ville_aff}",
            "adresse": "Annuaire + avis patients + prise de RDV",
            "note":    "📞 Comparateur de professionnels",
            "ouvert":  "🌐 mondocteur.fr",
            "lien":    f"https://www.mondocteur.fr/recherche?specialite={type_slug}&ville={ville_slug}"
        },
        {
            "nom":     "Ordre des Psychologues — Annuaire officiel",
            "adresse": "Tous les psychologues agréés en France",
            "note":    "📞 01 55 58 36 80",
            "ouvert":  "🌐 ordres-psychologues.fr",
            "lien":    f"https://www.ordres-psychologues.fr/annuaire?ville={ville_slug}"
        },
        {
            "nom":     f"CMP (Centre Médico-Psychologique) — {ville_aff}",
            "adresse": "Consultation gratuite, sans avance de frais",
            "note":    "📞 Via votre médecin traitant",
            "ouvert":  "💡 Remboursé Sécurité Sociale",
            "lien":    ""
        },
    ]


def formater_pour_chat(resultats: list, ville: str, type_pro: str) -> str:
    ville_aff = ville.strip().capitalize()
    texte = f"Voici comment trouver un {type_pro} à {ville_aff} :\n\n"
    for i, pro in enumerate(resultats, 1):
        texte += f"{i}. {pro['nom']}\n"
        texte += f"   📍 {pro['adresse']}\n"
        texte += f"   {pro['note']} · {pro['ouvert']}\n"
        if pro.get("lien"):
            texte += f"   🔗 {pro['lien']}\n"
        texte += "\n"
    texte += "Souhaites-tu autre chose ?"
    return texte