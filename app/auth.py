from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app.database import User
from app.extensions import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("main.index"))
        else:
            flash("Credenciales incorrectas")
            return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe")
            return redirect(url_for("auth.register"))

        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash("Registro exitoso. Inicia sesión.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        nuevo_usuario = request.form.get("username")
        nueva_clave = request.form.get("password")

        if nuevo_usuario:
            existe = User.query.filter_by(username=nuevo_usuario).first()
            if existe and existe.id != current_user.id:
                flash("Ese nombre de usuario ya está en uso.")
                return redirect(url_for("auth.perfil"))
            current_user.username = nuevo_usuario

        if nueva_clave:
            hashed = generate_password_hash(nueva_clave)
            current_user.password = hashed

        db.session.commit()
        flash("Perfil actualizado correctamente.")
        return redirect(url_for("main.index"))

    return render_template("perfil.html")
