from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from io import BytesIO
from datetime import datetime
import os

from app.crypto_utils import encrypt_file, decrypt_file
from app.database import Backup
from app.extensions import db
from gdrive_upload import upload_to_drive


main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
@login_required
def index():
    query = request.args.get("q", "").lower()

    backups = Backup.query.filter_by(user_id=current_user.id, eliminado=False).order_by(Backup.timestamp.desc()).all()


    files = []
    for backup in backups:
        if query and query not in backup.filename.lower():
            continue
        files.append({
            "name": backup.filename,
            "size": f"{backup.size_kb:.1f} KB",
            "date": backup.timestamp.strftime('%Y-%m-%d %H:%M')
        })

    return render_template("index.html", files=files, query=query)

@main.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("Nombre de archivo vacío.")
        return redirect(url_for("main.index"))

    raw_data = file.read()
    encrypted_data = encrypt_file(raw_data)

    filename = file.filename + ".enc"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    with open(path, "wb") as f:
        f.write(encrypted_data)

    size_kb = os.path.getsize(path) / 1024
    now = datetime.now()

    # 👇 Subida automática a Google Drive
    try:
        drive_file_id = upload_to_drive(path, filename)
        flash(f"Archivo subido correctamente y respaldado en Google Drive. ID: {drive_file_id}")
    except Exception as e:
        flash(f"Error al subir a Google Drive: {e}")
        drive_file_id = None

    new_backup = Backup(
        filename=filename,
        size_kb=size_kb,
        timestamp=now,
        user_id=current_user.id
    )
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

    backup.eliminado = True  # 👈 Solo lo marca como eliminado
    db.session.commit()
    flash(f"Archivo '{filename}' movido a la papelera.")
    return redirect(url_for("main.index"))


@main.route("/historial")
@login_required
def historial():
    backups = Backup.query.filter_by(user_id=current_user.id).order_by(Backup.timestamp.desc()).all()

    registros = []
    for b in backups:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], b.filename)
        existe = os.path.isfile(full_path)
        registros.append({
            "name": b.filename,
            "size": f"{b.size_kb:.1f} KB",
            "date": b.timestamp.strftime('%Y-%m-%d %H:%M'),
            "status": "Disponible" if existe else "Eliminado"
        })

    return render_template("historial.html", registros=registros)

@main.route("/papelera")
@login_required
def papelera():
    backups = Backup.query.filter_by(user_id=current_user.id, eliminado=True).order_by(Backup.timestamp.desc()).all()

    archivos = []
    for b in backups:
        archivos.append({
            "name": b.filename,
            "size": f"{b.size_kb:.1f} KB",
            "date": b.timestamp.strftime('%Y-%m-%d %H:%M')
        })

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

