import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

email = os.environ.get("SMTP_EMAIL")
password = os.environ.get("SMTP_PASSWORD")

print(f"Tentative de connexion pour : {email}")

try:
    # On tente une connexion directe avec le port standard
    with smtplib.SMTP("142.250.27.108", 587) as server:
        server.starttls()
        server.login(email, password)
        print("-> CONNEXION RÉUSSIE ! Votre fichier .env est parfait.")
except Exception as e:
    print(f"-> ÉCHEC DE CONNEXION. L'erreur est : {e}")
