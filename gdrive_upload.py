import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Ruta al archivo JSON de credenciales de Google
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Scopes necesarios para subir archivos
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# 👇 ESTE es el ID REAL de tu carpeta SYSBACKUP en Google Drive
FOLDER_ID = '1Eki7GI_borhrGJ7myooNbmimLy3BXN24'  # ← SOLO el ID

# Autenticación con Google
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Servicio de Google Drive
drive_service = build('drive', 'v3', credentials=credentials)

def upload_to_drive(filepath, filename):
    """Sube un archivo al Drive dentro de la carpeta SYSBACKUP y devuelve el ID"""
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
