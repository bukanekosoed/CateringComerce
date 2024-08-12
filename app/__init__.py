from flask import Flask,render_template
from config import Config
from pymongo import MongoClient
from flask_session import Session

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Setup MongoDB
    client = MongoClient(app.config['MONGO_URI'])
    app.db = client[app.config['DB_NAME']]

    # Debugging: cek apakah koneksi berhasil
    try:
        app.db.command('ping')  # Ping database untuk memverifikasi koneksi
        print("MongoDB connected successfully")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

    # Setup session
    Session(app)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    # Import and register blueprints
    from .auth import auth_bp
    from .user import user_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/dashboard')
    app.register_blueprint(user_bp)

    return app
