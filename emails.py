# emails.py — Envoi d'emails via Gmail

import smtplib
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

MAIL_EMAIL    = os.getenv("MAIL_EMAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


def generer_code() -> str:
    """Génère un code de confirmation à 6 chiffres."""
    return str(random.randint(100000, 999999))


def envoyer_email(destinataire: str, sujet: str, corps_html: str) -> bool:
    """Envoie un email via Gmail."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = sujet
        msg["From"]    = f"MAI — My AI <{MAIL_EMAIL}>"
        msg["To"]      = destinataire

        msg.attach(MIMEText(corps_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as serveur:
            serveur.login(MAIL_EMAIL, MAIL_PASSWORD)
            serveur.sendmail(MAIL_EMAIL, destinataire, msg.as_string())

        return True
    except Exception as e:
        print(f"Erreur envoi email : {e}")
        return False


def envoyer_confirmation(prenom: str, email: str, code: str) -> bool:
    """Email de confirmation d'inscription avec code."""
    corps = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">

      <div style="background: #1a73e8; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 32px;">🤍 MAI</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0;">My AI — Ton espace d'écoute</p>
      </div>

      <div style="background: white; padding: 32px; border-radius: 0 0 12px 12px;
                  border: 1px solid #e0e0e0;">
        <h2 style="color: #1a1a2e;">Bonjour {prenom} 👋</h2>
        <p style="color: #555; line-height: 1.6;">
          Merci de rejoindre MAI ! Pour confirmer ton adresse email,
          utilise le code ci-dessous dans l'application :
        </p>

        <div style="background: #f0f4ff; border-radius: 12px; padding: 24px;
                    text-align: center; margin: 24px 0;">
          <p style="color: #666; font-size: 14px; margin: 0 0 8px;">Ton code de confirmation</p>
          <h1 style="color: #1a73e8; font-size: 48px; margin: 0;
                     letter-spacing: 8px;">{code}</h1>
          <p style="color: #999; font-size: 12px; margin: 8px 0 0;">
            Ce code expire dans 15 minutes
          </p>
        </div>

        <p style="color: #555; font-size: 13px; line-height: 1.6;">
          Si tu n'as pas créé de compte sur MAI, ignore cet email.
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
          MAI ne remplace pas un professionnel de santé.<br>
          Urgence : 15 · Prévention suicide : 3114
        </p>
      </div>

    </div>
    """
    return envoyer_email(email, "🤍 MAI — Ton code de confirmation", corps)


def envoyer_alerte_proche(
    prenom_utilisateur: str,
    email_proche: str,
    latitude: float = None,
    longitude: float = None
) -> bool:
    """Email d'alerte au proche avec localisation si disponible."""

    # Construire le bloc localisation
    if latitude and longitude:
        lien_maps = f"https://www.google.com/maps?q={latitude},{longitude}"
        bloc_localisation = f"""
        <div style="background: #fff8e1; border-left: 4px solid #f57f17;
                    padding: 16px; border-radius: 8px; margin: 20px 0;">
          <p style="color: #f57f17; font-weight: bold; margin: 0 0 8px;">
            📍 Localisation au moment du message
          </p>
          <p style="color: #333; margin: 0 0 12px;">
            Coordonnées : {latitude:.6f}, {longitude:.6f}
          </p>
          <a href="{lien_maps}"
             style="background: #f57f17; color: white; padding: 10px 20px;
                    border-radius: 8px; text-decoration: none; font-weight: bold;">
            Voir sur Google Maps →
          </a>
        </div>
        """
    else:
        bloc_localisation = """
        <div style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 20px 0;">
          <p style="color: #999; margin: 0;">
            📍 Localisation non disponible
          </p>
        </div>
        """

    corps = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">

      <div style="background: #c62828; padding: 24px;
                  border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">
          🤍 MAI — Message important
        </h1>
      </div>

      <div style="background: white; padding: 32px;
                  border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0;">

        <div style="background: #ffebee; border-left: 4px solid #c62828;
                    padding: 16px; border-radius: 8px; margin-bottom: 24px;">
          <p style="color: #c62828; font-weight: bold; margin: 0;">
            ⚠️ Message de soutien — À lire avec attention
          </p>
        </div>

        <p style="color: #333; line-height: 1.6;">
          Bonjour,<br><br>
          <strong>{prenom_utilisateur}</strong> vous a désigné(e) comme personne
          de confiance sur MAI (My AI). MAI a détecté une situation de détresse
          émotionnelle intense et vous en informe conformément au choix de
          <strong>{prenom_utilisateur}</strong>.
        </p>

        {bloc_localisation}

        <div style="background: #f0f4ff; border-radius: 12px;
                    padding: 20px; margin: 24px 0;">
          <p style="color: #1a73e8; font-weight: bold; margin: 0 0 8px;">
            Ce que vous pouvez faire maintenant :
          </p>
          <ul style="color: #333; line-height: 2; margin: 0; padding-left: 20px;">
            <li>Contacter <strong>{prenom_utilisateur}</strong> immédiatement</li>
            <li>L'écouter sans jugement</li>
            <li>L'accompagner vers une aide professionnelle</li>
          </ul>
        </div>

        <div style="background: #ffebee; border-radius: 12px;
                    padding: 20px; margin: 24px 0;">
          <p style="color: #c62828; font-weight: bold; margin: 0 0 8px;">
            Numéros d'urgence :
          </p>
          <p style="color: #333; margin: 0; line-height: 1.8;">
            🆘 SAMU : <strong>15</strong><br>
            💙 Prévention suicide : <strong>3114</strong><br>
            🚨 Police : <strong>17</strong>
          </p>
        </div>

        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
          Envoyé automatiquement par MAI — My AI<br>
          avec l'accord de {prenom_utilisateur}.
        </p>
      </div>
    </div>
    """
    return envoyer_email(
        email_proche,
        f"🤍 MAI — {prenom_utilisateur} a besoin de soutien",
        corps
    )
    
def envoyer_reset_mdp(prenom: str, email: str, code: str) -> bool:
    """Email de réinitialisation du mot de passe."""
    corps = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;">
      <div style="background: #1a73e8; padding: 24px; border-radius: 12px 12px 0 0;
                  text-align: center;">
        <h1 style="color: white; margin: 0;">🔑 MAI — Réinitialisation</h1>
      </div>
      <div style="background: white; padding: 32px; border-radius: 0 0 12px 12px;
                  border: 1px solid #e0e0e0;">
        <h2 style="color: #1a1a2e;">Bonjour {prenom},</h2>
        <p style="color: #555; line-height: 1.6;">
          Tu as demandé à réinitialiser ton mot de passe. Utilise ce code :
        </p>
        <div style="background: #f0f4ff; border-radius: 12px; padding: 24px;
                    text-align: center; margin: 24px 0;">
          <p style="color: #666; font-size: 14px; margin: 0 0 8px;">Code de réinitialisation</p>
          <h1 style="color: #1a73e8; font-size: 48px; margin: 0;
                     letter-spacing: 8px;">{code}</h1>
          <p style="color: #999; font-size: 12px; margin: 8px 0 0;">
            Ce code expire dans 15 minutes
          </p>
        </div>
        <p style="color: #555; font-size: 13px;">
          Si tu n'as pas fait cette demande, ignore cet email.
        </p>
      </div>
    </div>
    """
    return envoyer_email(email, "🔑 MAI — Réinitialisation de ton mot de passe", corps)