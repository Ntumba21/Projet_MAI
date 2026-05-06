# mai.py — La logique de conversation de MAI

import os
from groq import Groq
from dotenv import load_dotenv
from scoring import calculer_score

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def construire_systeme(niveau: str, age: int = 99) -> str:
    """
    Retourne le prompt système adapté au niveau de gravité.
    C'est ce qui dit à l'IA comment se comporter.
    """

    base = """Tu es MAI (My AI), un chatbot de soutien émotionnel bienveillant.
Tu parles en français, avec un ton chaleureux et empathique.
Tu ne poses JAMAIS de diagnostic médical.
Tu ne remplaces pas un professionnel de santé.
Tu poses UNE seule question à la fois, jamais plusieurs d'un coup.
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
Propose de rechercher des professionnels dans sa ville.
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
    'messages' = liste de tous les messages échangés jusque-là.
    """

    # On analyse le dernier message de l'utilisateur
    dernier_message = messages[-1]["content"] if messages else ""
    resultat_score = calculer_score(dernier_message, age)
    niveau = resultat_score["niveau"]

    # On construit le prompt système selon la gravité
    systeme = construire_systeme(niveau, age)

    # On prépare la conversation complète pour l'IA
    conversation = [{"role": "system", "content": systeme}] + messages

    # On appelle l'API groq
    reponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # modèle rapide et pas cher
        messages=conversation,
        max_tokens=500,
        temperature=0.7  # un peu de créativité mais pas trop
    )

    texte_reponse = reponse.choices[0].message.content

    return {
        "reponse": texte_reponse,
        "niveau": niveau,
        "score": resultat_score["score"]
    }