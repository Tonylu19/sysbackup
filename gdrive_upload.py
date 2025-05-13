import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes necesarios para subir a Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ID de la carpeta SYSBACKUP en tu Google Drive
FOLDER_ID = '1Eki7GI_borhrGJ7myooNbmimLy3BXN24'  # ← Usa el tuyo aquí

# Leer credenciales desde variable de entorno segura
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')

# Crear objeto de autenticación desde el JSON embebido
credentials = service_account.Credentials.from_service_account_info(
    json.loads(GOOGLE_CREDENTIALS),
    scopes=SCOPES
)

# Servicio de Google Drive
drive_service = build('drive', 'v3', credentials=credentials)

def upload_to_drive(filepath, filename):
    """Sube un archivo al Drive dentro de la carpeta SYSBACKUP y devuelve su ID"""
    file_metadata = {
        'name': filename,
        'parents': [FOLDER_ID]
    }
    media = MediaFileUpload(filepath, mimetype='application/octet-stream')

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return file.get('id')
