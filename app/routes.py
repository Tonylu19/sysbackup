from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from io import BytesIO
from datetime import datetime
import os

from app.crypto_utils import encrypt_file, decrypt_file
from app.database import Backup
from app.extensions import db

main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
@login_required
def index():
    query = request.args.get("q", "").lower()

    backups = Backup.query.filter_by(user_id=current_user.id).order_by(Backup.timestamp.desc()).all()

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

    new_backup = Backup(filename=filename, size_kb=size_kb, timestamp=now, user_id=current_user.id)
    db.session.add(new_backup)
    db.session.commit()

    flash(f"Archivo '{file.filename}' subido correctamente.")
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

    db.session.delete(backup)
    db.session.commit()
    flash(f"Archivo '{filename}' eliminado.")
    return redirect(url_for("main.index"))
