
from tools.gmail_tool import envoyer_email

destinataire = input("Adresse e-mail de destination : ")

resultat = envoyer_email(
    destinataire=destinataire,
    objet="Test Gmail API",
    contenu="Bonjour, ceci est un e-mail de test envoyé via Gmail API."
)

print(resultat)
