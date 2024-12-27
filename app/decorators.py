from flask import redirect, url_for, session, flash, request
from functools import wraps
from .models import Admin, Users

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Harap login untuk mengakses fitur ini.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            session['next_url'] = request.url
            flash('Harap login untuk mengakses fitur ini.', 'warning')
            return redirect(url_for('auth.login'))

        if not Admin.objects(id=user_id).first():
            session['next_url'] = request.url

            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        if not user_id:
            # Allow access to public pages if the user is not logged in
            if request.endpoint in ['main.index', 'main.shop', 'main.news', "main.order" ]:
                return f(*args, **kwargs)
            
            session['next_url'] = request.url
            flash('You need to log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = Users.objects(id=user_id).first()
        admin = Admin.objects(id=user_id).first()

        if admin:
            flash("Admin cannot access user pages.", "danger")
            return redirect(url_for('admin.index'))
        
        if not user:
            session['next_url'] = request.url
            flash('User access required.', 'warning')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function
