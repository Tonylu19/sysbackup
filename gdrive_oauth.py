import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Detectar entorno y permitir HTTP solo si estás en local
redirect_uri = os.getenv("REDIRECT_URI", "")
if redirect_uri.startswith("http://"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_flow():
    """
    Configura el flujo OAuth 2.0 dinámicamente, leyendo las variables de entorno.
    """
    try:
        credentials = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        flow = Flow.from_client_config(
            credentials,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow
    except Exception as e:
        raise RuntimeError(f"Error creando flujo OAuth: {e}")

def save_user_token(user_id, credentials):
    """
    Guarda el token de acceso del usuario autenticado.
    """
    os.makedirs("tokens", exist_ok=True)
    token_path = os.path.join("tokens", f"user_{user_id}.json")
    with open(token_path, "w") as token_file:
        token_file.write(credentials.to_json())

def create_drive_service(user_id):
    """
    Usa el token guardado del usuario para crear el servicio de Google Drive.
    """
    token_path = os.path.join("tokens", f"user_{user_id}.json")
    if not os.path.exists(token_path):
        return None

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    return build("drive", "v3", credentials=creds)
