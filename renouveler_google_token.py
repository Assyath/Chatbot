from tools.google_auth import obtenir_google_credentials

creds = obtenir_google_credentials()

print("Authentification Google réussie.")
print("Jeton obtenu :", bool(creds.token))
print("Jeton de renouvellement obtenu :", bool(creds.refresh_token))
print("Autorisations :", creds.scopes)