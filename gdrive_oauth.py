import os
import json
import pickle
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ⚠️ Permitir HTTP solo en desarrollo local
if not os.getenv("RENDER"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_flow():
    # ✅ Aquí ya viene con "web", no la envuelvas de nuevo
    credentials = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

    flow = Flow.from_client_config(
        credentials,
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URI")
    )
    return flow

def save_user_token(user_id, credentials):
    token_path = os.path.join("tokens", f"user_{user_id}.json")
    with open(token_path, "w") as f:
        f.write(credentials.to_json())

def create_drive_service(user_id):
    token_path = os.path.join("tokens", f"user_{user_id}.json")
    if not os.path.exists(token_path):
        return None
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    return build("drive", "v3", credentials=creds)