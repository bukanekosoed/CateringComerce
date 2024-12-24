from flask import Flask, render_template, session
from config import Config
from flask_login import LoginManager
from flask_session import Session
from flask_pymongo import PyMongo
from .models import  Users, Admin
import pytz

# Import and register blueprints
from .auth import auth_bp,oauth
from .user import user_bp
from .admin import admin_bp
from .image import image_bp
from .notification import notification_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MONGO_URI"]
    app.config["SECRET_KEY"]
    app.config["DB_NAME"]
    app.config["SESSION_TYPE"]
    app.config["SESSION_MONGODB_DB"]
    app.config["SESSION_MONGODB_COLLECT"]
    app.config["MIDTRANS_SERVER_KEY"]
    app.config["MIDTRANS_CLIENT_KEY"]

    # Inisialisasi Flask-PyMongo
    mongo = PyMongo(app)

    # Konfigurasi Flask-Session untuk MongoDB
    app.config['SESSION_TYPE'] = 'mongodb'
    app.config['SESSION_MONGODB'] = mongo.cx  # Instance MongoClient dari PyMongo
    app.config['SESSION_MONGODB_DB'] = 'mydatabase'  # Nama database yang digunakan
    app.config['SECRET_KEY'] = 'your_secret_key'  # Ganti dengan kunci rahasia Anda

    # Inisialisasi Flask-Session
    Session(app)
    oauth.init_app(app)
    # Inisialisasi Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        # Try to load the user from Users collection
        user = Users.objects(id=user_id).first()
        if user:
            return user
        
        # Fallback to Admins collection if not found in Users
        admin = Admin.objects(id=user_id).first()
        if admin:
            return admin

        return None
    
    # Setup session filters
    @app.template_filter('idr')
    def idr_format(value):
        return f"Rp {value:,.0f}".replace(',', '.')
    
    @app.template_filter('gmt7')
    def gmt7_filter(value):
        indonesia_tz = pytz.timezone('Asia/Jakarta')
        if value is not None:
            if value.tzinfo is None:  # Jika waktu tidak memiliki zona waktu
                value = pytz.utc.localize(value)  # Menganggap waktu UTC
            value = value.astimezone(indonesia_tz)
        return value.strftime('%d %b %Y, %H:%M WIB')

    @app.template_filter('to_string')
    def to_string(value):
        return str(value)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

   

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/dashboard')
    app.register_blueprint(notification_bp, url_prefix='/api')
    app.register_blueprint(image_bp)
    app.register_blueprint(user_bp)

    def create_admin_user():
        if not Admin.objects(email="admin@admin.com"):
            admin = Admin(
                name="Default Admin",
                email="admin@admin.com"
            )
            admin.set_password("admin123@1234")  # Set hashed password
            admin.save()
            print("Admin user created: admin@example.com/admin123")
        else:
            print("Admin user already exists.")

    create_admin_user()
    return app
