
from tools.google_auth import SCOPES, ROOT_DIR
from google_auth_oauthlib.flow import InstalledAppFlow

credentials_path = ROOT_DIR / "credentials.json"
token_path = ROOT_DIR / "token.json"

flow = InstalledAppFlow.from_client_secrets_file(
    str(credentials_path),
    SCOPES
)

creds = flow.run_local_server(port=0, prompt="consent")

token_path.write_text(creds.to_json(), encoding="utf-8")

print("Authentification Google réussie.")
print("Jeton obtenu :", bool(creds.token))
print("Jeton de renouvellement obtenu :", bool(creds.refresh_token))
