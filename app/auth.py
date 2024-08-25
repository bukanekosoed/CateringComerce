from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from .models import Users,Admin


# Blueprint untuk autentikasi
auth_bp = Blueprint('auth', __name__)

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

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))

        # Check if user with email already exists
        existing_user = Users.objects(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
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
            flash('Registration successful! Please login.', 'primary')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('auth.register'))
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Fetch the user from the database
        user = Users.objects(email=email).first()
        admin = Admin.objects(email=email).first()
        
        # Check if the user exists and if the password is correct
        if user and user.check_password(password):
            session['user_id'] = str(user.id)
            session['user_role'] = 'user'
            flash('Login successful!', 'primary')
            next_url = session.pop('next_url', url_for('main.index'))
            return redirect(next_url)
        
        if admin and admin.check_password(password):
            session['user_id'] = str(admin.id)
            session['user_role'] = 'admin'
            flash('Login successful!', 'success')
            next_url = session.pop('next_url', url_for('admin.index'))
            return redirect(next_url)
        
        flash('Invalid email or password.', 'danger')
            
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out successfully.', 'primary')
    return redirect(url_for('main.index'))