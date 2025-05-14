import os
import json
import pathlib
from flask import current_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ✅ Esto permite HTTP solo si estás en desarrollo
if not os.getenv("RENDER"):  # Si NO estás en producción
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# 📁 Ruta al archivo client_secret.json
CLIENT_SECRET_FILE = os.path.join(pathlib.Path(__file__).parent.resolve(), 'client_secret.json')

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Crea el flujo OAuth para conexión Drive
def get_flow():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri="http://127.0.0.1:10000/oauth2callback"  # ⚠️ Cambia por https://sysbackup.onrender.com en producción
    )
    return flow

# Guarda el token del usuario conectado
def save_user_token(user_id, credentials):
    token_path = os.path.join("tokens", f"user_{user_id}.json")
    with open(token_path, "w") as f:
        f.write(credentials.to_json())

# Crea el servicio de Drive para subir archivos
def create_drive_service(user_id):
    token_path = os.path.join("tokens", f"user_{user_id}.json")
    if not os.path.exists(token_path):
        return None

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service
