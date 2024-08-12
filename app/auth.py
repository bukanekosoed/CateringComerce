from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegistrationForm

# Blueprint untuk autentikasi
auth_bp = Blueprint('auth', __name__)

# Rute untuk login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = current_app.db  # Akses db dari aplikasi saat ini
        user = db.users.find_one({"email": form.email.data})
        if user and check_password_hash(user['password'], form.password.data):
            flash('Login successful.', 'success')
            return redirect(url_for('main.index'))  # Ganti 'main.index' dengan route yang sesuai
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    return render_template('auth/login.html', form=form)

# Rute untuk registrasi
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        db = current_app.db  # Akses db dari aplikasi saat ini

        # Cek apakah email sudah ada di database
        existing_user = db.users.find_one({"email": form.email.data})
        if existing_user:
            flash('Email is already in use. Please choose a different email.', 'danger')
        else:
            hashed_password = generate_password_hash(form.password.data)
            user_data = {
                'email': form.email.data,
                'password': hashed_password
            }
            db.users.insert_one(user_data)
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/register.html', form=form)
