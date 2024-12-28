from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from .models import Users,Admin
from authlib.integrations.flask_client import OAuth
import re
auth_bp = Blueprint('auth', __name__)

# Inisialisasi OAuth
oauth = OAuth()


@auth_bp.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        profile_image = request.files.get('profile_image')

        name_pattern = r'^[A-Za-z\s]+$'  
        if not re.match(name_pattern, name):
            flash('Nama Tidak Valid. Pastikan nama hanya mengandung huruf dan spasi.', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Kata Sandi Tidak Sama', 'danger')
            return redirect(url_for('auth.register'))

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Format Email Tidak Valid. Pastikan email memiliki domain (contoh: user@domain.com)', 'danger')
            return redirect(url_for('auth.register'))

        # Validate password format
        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
        if not re.match(password_pattern, password):
            flash('Kata sandi harus memiliki minimal 8 karakter, termasuk huruf besar, huruf kecil, angka, dan simbol.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if user with email already exists
        existing_user = Users.objects(email=email).first()
        if existing_user:
            flash('Alamat Email Sudah Digunakan', 'danger')
            return redirect(url_for('auth.register'))

        # Create a new user object
        new_user = Users(
            name=name,
            email=email,
            phone=phone,
            profile_image=profile_image
        )
        new_user.set_password(password)  # Hash the password

        # Save the user
        try:
            new_user.save()
            flash('Registrasi Berhasil! Silahkan Login', 'primary')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('auth.register'))
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Ambil user dari database
        user = Users.objects(email=email).first()
        admin = Admin.objects(email=email).first()
        
        # Jika email tidak ditemukan pada user maupun admin
        if not user and not admin:
            flash('Email tidak ditemukan. Silakan registrasi terlebih dahulu.', 'warning')
        else:
            # Periksa apakah user ada dan password benar
            if user and user.check_password(password):
                session['user_id'] = str(user.id)
                session['user_role'] = 'user'
                flash('Login berhasil!', 'primary')
                next_url = session.pop('next_url', url_for('main.index'))
                return redirect(next_url)
            
            # Periksa jika admin ada dan password benar
            if admin and admin.check_password(password):
                session['user_id'] = str(admin.id)
                session['user_role'] = 'admin'
                flash('Login berhasil!', 'success')
                next_url = session.pop('next_url', url_for('admin.index'))
                return redirect(next_url)
            
            # Jika password salah
            flash('Email atau password salah.', 'danger')
            
    return render_template('auth/login.html')




# Route untuk logout
@auth_bp.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('Anda Berhasil Keluar', 'primary')
    return redirect(url_for('main.index'))


