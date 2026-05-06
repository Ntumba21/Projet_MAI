# test_mai.py — Tester MAI en conversation réelle dans le terminal

import requests
import sys

URL = "http://127.0.0.1:8000/chat"

# Couleurs pour rendre le terminal plus lisible
BLEU    = "\033[94m"
VERT    = "\033[92m"
JAUNE   = "\033[93m"
ROUGE   = "\033[91m"
RESET   = "\033[0m"
GRAS    = "\033[1m"

def couleur_niveau(niveau):
    """Affiche le niveau de gravité avec une couleur adaptée."""
    couleurs = {
        "soutien_leger":    VERT  + "🟢 Soutien léger",
        "orientation_pro":  JAUNE + "🟡 Orientation professionnelle",
        "urgence":          ROUGE + "🔴 Urgence humaine",
        "urgence_mineur":   ROUGE + "🔴 Urgence — Protocole mineur",
    }
    return couleurs.get(niveau, niveau) + RESET


def parler_a_mai(messages, age=99):
    """Envoie un message au serveur MAI et retourne la réponse."""
    try:
        reponse = requests.post(URL, json={
            "messages": messages,
            "age": age
        })
        return reponse.json()
    except Exception as e:
        print(f"{ROUGE}Erreur : le serveur ne répond pas. Lance d'abord uvicorn !{RESET}")
        sys.exit(1)


def conversation_libre(age=99):
    """
    Mode conversation libre — tu parles à MAI comme dans l'appli finale.
    Tape 'quitter' pour arrêter.
    """
    print(f"\n{GRAS}{'='*50}{RESET}")
    print(f"{BLEU}{GRAS}  Conversation avec MAI — Mode libre{RESET}")
    if age < 18:
        print(f"{JAUNE}  ⚠️  Protocole mineur actif (âge : {age} ans){RESET}")
    print(f"{GRAS}{'='*50}{RESET}")
    print(f"  Tape {GRAS}'quitter'{RESET} pour arrêter\n")

    historique = []

    # Message de bienvenue de MAI
    debut = parler_a_mai([{
        "role": "user",
        "content": "Bonjour"
    }], age)
    print(f"{BLEU}{GRAS}MAI :{RESET} {debut['reponse']}\n")
    historique.append({"role": "user", "content": "Bonjour"})
    historique.append({"role": "assistant", "content": debut['reponse']})

    while True:
        # Saisie utilisateur
        try:
            user_input = input(f"{VERT}{GRAS}Toi :{RESET} ").strip()
        except KeyboardInterrupt:
            print(f"\n{JAUNE}Conversation terminée.{RESET}")
            break

        if user_input.lower() in ["quitter", "exit", "quit", ""]:
            print(f"\n{BLEU}MAI : Prends soin de toi 💙{RESET}")
            break

        # Ajout du message à l'historique
        historique.append({"role": "user", "content": user_input})

        # Envoi au serveur
        resultat = parler_a_mai(historique, age)

        # Affichage de la réponse
        print(f"\n{BLEU}{GRAS}MAI :{RESET} {resultat['reponse']}")
        print(f"  {GRAS}Niveau :{RESET} {couleur_niveau(resultat['niveau'])}  "
              f"{GRAS}Score :{RESET} {resultat['score']}\n")

        # Ajout de la réponse à l'historique
        historique.append({
            "role": "assistant",
            "content": resultat['reponse']
        })


def tester_cas(nom_cas, messages_test, age=99):
    """
    Rejoue automatiquement un cas pratique de ton rapport.
    """
    print(f"\n{GRAS}{'='*50}{RESET}")
    print(f"{BLEU}{GRAS}  {nom_cas}{RESET}")
    if age < 18:
        print(f"{JAUNE}  ⚠️  Protocole mineur actif (âge : {age} ans){RESET}")
    print(f"{GRAS}{'='*50}{RESET}\n")

    historique = []

    for message_utilisateur in messages_test:
        # Affichage du message utilisateur
        print(f"{VERT}{GRAS}Toi :{RESET} {message_utilisateur}")

        # Ajout à l'historique
        historique.append({"role": "user", "content": message_utilisateur})

        # Envoi à MAI
        resultat = parler_a_mai(historique, age)

        # Affichage de la réponse
        print(f"{BLEU}{GRAS}MAI :{RESET} {resultat['reponse']}")
        print(f"  {GRAS}→ Niveau :{RESET} {couleur_niveau(resultat['niveau'])}  "
              f"{GRAS}Score :{RESET} {resultat['score']}\n")

        # Ajout de la réponse à l'historique
        historique.append({
            "role": "assistant",
            "content": resultat['reponse']
        })


def menu():
    """Menu principal du script de test."""
    print(f"\n{GRAS}{'='*50}")
    print("         MAI — Interface de test")
    print(f"{'='*50}{RESET}\n")
    print("  1. Conversation libre")
    print("  2. Cas 1 — Stress ponctuel (Élise, 23 ans)")
    print("  3. Cas 2 — Anxiété persistante (Jean, 30 ans)")
    print("  4. Cas 3 — Addiction (Rob, 25 ans)")
    print("  5. Cas 4 — Burn-out (Eri, 34 ans)")
    print("  6. Cas 5 — Urgence mineur (Annie, 12 ans)")
    print("  0. Quitter\n")

    choix = input("  Ton choix : ").strip()
    return choix


# ─── CAS PRATIQUES (repris de ton rapport) ───────────────────────────────────

CAS_1 = [
    "Bonjour MAI, moi ça ne va pas fort",
    "Je me sens un peu sous pression ces derniers jours",
    "Je pense que c'est le travail ou l'école, je suis perdu",
    "Honnêtement je ne sais pas, je dirais 5 sur 10",
    "Jouer au foot avec mes amis",
]

CAS_2 = [
    "Bonjour MAI, je me sens anxieux depuis quelques semaines et je ne sais pas quoi faire",
    "Non je ne me sens pas à l'aise d'en parler à un proche",
    "Non mais surtout je ne sais pas à qui m'adresser",
    "J'aimerais une liste pour le Kremlin-Bicêtre et ses environs",
]

CAS_3 = [
    "Bonjour MAI, que penses-tu des personnes qui ont des addictions ?",
    "Tu ne les vois pas comme des personnes faibles ?",
    "Moi j'ai une addiction à la pornographie que j'essaie encore et encore d'arrêter",
    "Non je crains le jugement, je ne sais pas trop",
    "Oui mais à qui m'adresser ?",
    "Vas-y explique moi la différence",
    "Un psychanalyste vu que c'est un schéma qui se répète",
]

CAS_4 = [
    "Hello MAI, je ne vais pas fort, je me sens mal et très épuisé",
    "Je pense que c'est mon travail, je n'ai plus de motivation et je dors mal",
    "Oui ça dure depuis longtemps",
    "Oui j'en ai parlé à des proches mais ils ne comprennent pas",
    "Oui je veux bien que tu m'aides à trouver quelqu'un",
]

CAS_5 = [
    "MAI j'ai peur de faire une bêtise",
    "Je n'en peux plus, j'ai parfois envie d'en finir",
    "Non je ne pense pas, ils me jugeront",
    "Je me fais harceler par une fille à l'école",
    "Oui j'aimerais bien de l'aide",
]


# ─── PROGRAMME PRINCIPAL ─────────────────────────────────────────────────────

if __name__ == "__main__":
    while True:
        choix = menu()

        if choix == "1":
            age_str = input("\n  Quel âge as-tu ? (appuie sur Entrée pour passer) : ").strip()
            age = int(age_str) if age_str.isdigit() else 99
            conversation_libre(age)

        elif choix == "2":
            tester_cas("Cas 1 — Stress ponctuel — Élise, 23 ans", CAS_1, age=23)

        elif choix == "3":
            tester_cas("Cas 2 — Anxiété persistante — Jean, 30 ans", CAS_2, age=30)

        elif choix == "4":
            tester_cas("Cas 3 — Addiction — Rob, 25 ans", CAS_3, age=25)

        elif choix == "5":
            tester_cas("Cas 4 — Burn-out — Eri, 34 ans", CAS_4, age=34)

        elif choix == "6":
            tester_cas("Cas 5 — Urgence mineur — Annie, 12 ans", CAS_5, age=12)

        elif choix == "0":
            print(f"\n{BLEU}Au revoir 💙{RESET}\n")
            break

        else:
            print(f"{JAUNE}Choix invalide, réessaie.{RESET}")