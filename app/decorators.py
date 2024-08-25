from functools import wraps
from flask import redirect, url_for, session, flash,request
from .models import Admin,Users

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Fetch user_id from the session
        user_id = session.get('user_id')
        if not user_id:
            session['next_url'] = request.url
            flash('You need to log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        # Check if the user is an admin
        if not Admin.objects(id=user_id).first():
            session['next_url'] = request.url
            flash('Admin access required.', 'warning')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        if not user_id:
            # Allow access to public pages if the user is not logged in
            if request.endpoint in ['main.index', 'main.shop', 'main.order', 'main.profile']:
                return f(*args, **kwargs)
            
            # Redirect to login if user is required
            session['next_url'] = request.url
            flash('You need to log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if the user is an admin
        user = Users.objects(id=user_id).first()
        admin = Admin.objects(id=user_id).first()
        
        if admin:
            # Redirect admin to the admin dashboard
            flash("Admin cannot access user pages.", "danger")
            return redirect(url_for('admin.index'))
        
        if not user:
            # If no user is found, redirect to login page
            session['next_url'] = request.url
            flash('Users access required.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function