from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from io import BytesIO
from datetime import datetime
import os

from app.crypto_utils import encrypt_file, decrypt_file
from app.database import Backup
from app.extensions import db
from gdrive_oauth import get_flow, save_user_token, create_drive_service
from werkzeug.utils import secure_filename
from googleapiclient.http import MediaFileUpload

main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
@login_required
def index():
    query = request.args.get("q", "").lower()
    backups = Backup.query.filter_by(user_id=current_user.id, eliminado=False).order_by(Backup.timestamp.desc()).all()
    files = [{
        "name": b.filename,
        "size": f"{b.size_kb:.1f} KB",
        "date": b.timestamp.strftime('%Y-%m-%d %H:%M')
    } for b in backups if not query or query in b.filename.lower()]
    return render_template("index.html", files=files, query=query)

@main.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files or request.files["file"].filename == "":
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    original_filename = secure_filename(file.filename)
    encrypted_data = encrypt_file(file.read())
    encrypted_filename = original_filename + ".enc"
    local_path = os.path.join(current_app.config["UPLOAD_FOLDER"], encrypted_filename)

    with open(local_path, "wb") as f:
        f.write(encrypted_data)

    drive_service = create_drive_service(current_user.id)
    if drive_service:
        try:
            metadata = {"name": encrypted_filename}
            media = MediaFileUpload(local_path, mimetype="application/octet-stream")
            drive_service.files().create(body=metadata, media_body=media).execute()
            flash("Archivo subido a Google Drive.")
        except Exception as e:
            flash(f"Error al subir a Google Drive: {e}")
    else:
        flash("Tu cuenta no está conectada a Google Drive.")

    size_kb = os.path.getsize(local_path) / 1024
    now = datetime.now()
    new_backup = Backup(filename=encrypted_filename, size_kb=size_kb, timestamp=now, user_id=current_user.id)
    db.session.add(new_backup)
    db.session.commit()

    return redirect(url_for("main.index"))

@main.route("/download/<filename>")
@login_required
def download_file(filename):
    backup = Backup.query.filter_by(filename=filename, user_id=current_user.id).first()
    if not backup:
        flash("Archivo no encontrado o no autorizado.")
        return redirect(url_for("main.index"))

    enc_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(enc_path):
        flash("El archivo no existe en el servidor.")
        return redirect(url_for("main.index"))

    with open(enc_path, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)
    original_name = filename.replace(".enc", "")

    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=original_name
    )

@main.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_file(filename):
    backup = Backup.query.filter_by(filename=filename, user_id=current_user.id).first()
    if not backup:
        flash("No tienes permiso para eliminar este archivo.")
        return redirect(url_for("main.index"))

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

    backup.eliminado = True
    db.session.commit()
    flash(f"Archivo '{filename}' movido a la papelera.")
    return redirect(url_for("main.index"))

@main.route("/historial")
@login_required
def historial():
    backups = Backup.query.filter_by(user_id=current_user.id).order_by(Backup.timestamp.desc()).all()
    registros = [{
        "name": b.filename,
        "size": f"{b.size_kb:.1f} KB",
        "date": b.timestamp.strftime('%Y-%m-%d %H:%M'),
        "status": "Disponible" if os.path.isfile(os.path.join(current_app.config["UPLOAD_FOLDER"], b.filename)) else "Eliminado"
    } for b in backups]
    return render_template("historial.html", registros=registros)

@main.route("/papelera")
@login_required
def papelera():
    backups = Backup.query.filter_by(user_id=current_user.id, eliminado=True).order_by(Backup.timestamp.desc()).all()
    archivos = [{
        "name": b.filename,
        "size": f"{b.size_kb:.1f} KB",
        "date": b.timestamp.strftime('%Y-%m-%d %H:%M')
    } for b in backups]
    return render_template("papelera.html", archivos=archivos)

@main.route("/restaurar/<filename>", methods=["POST"])
@login_required
def restaurar_file(filename):
    backup = Backup.query.filter_by(filename=filename, user_id=current_user.id).first()
    if not backup:
        flash("Archivo no encontrado.")
        return redirect(url_for("main.papelera"))

    backup.eliminado = False
    db.session.commit()
    flash(f"Archivo '{filename}' restaurado.")
    return redirect(url_for("main.papelera"))

@main.route("/connect_drive")
@login_required
def connect_drive():
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

@main.route("/oauth2callback")
@login_required
def oauth2callback():
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)
    save_user_token(current_user.id, flow.credentials)
    flash("Google Drive conectado exitosamente.")
    return redirect(url_for("main.index"))