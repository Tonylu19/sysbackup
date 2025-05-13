from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required
import os
from io import BytesIO
from app.crypto_utils import encrypt_file, decrypt_file
from datetime import datetime
from flask import request


main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
@login_required
def index():
    folder = current_app.config["UPLOAD_FOLDER"]
    query = request.args.get("q", "").lower()
    files = []

    for filename in os.listdir(folder):
        if filename.endswith(".enc"):
            if query and query not in filename.lower():
                continue

            path = os.path.join(folder, filename)
            size_kb = os.path.getsize(path) / 1024
            timestamp = os.path.getmtime(path)
            files.append({
                "name": filename,
                "size": f"{size_kb:.1f} KB",
                "date": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
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

    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename + ".enc")
    with open(output_path, "wb") as f:
        f.write(encrypted_data)

    flash(f"Archivo '{file.filename}' cifrado y guardado exitosamente.")
    return redirect(url_for("main.index"))

@main.route("/download/<filename>")
@login_required
def download_file(filename):
    enc_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    if not os.path.isfile(enc_path):
        flash("El archivo no existe.")
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
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    if os.path.isfile(file_path):
        os.remove(file_path)
        flash(f"Archivo '{filename}' eliminado.")
    else:
        flash("Archivo no encontrado.")

    return redirect(url_for("main.index"))
