from flask import Flask,render_template, session
from config import Config
from flask_session import Session

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Setup session
    Session(app)
    @app.template_filter('idr')
    def idr_format(value):
        return f"Rp {value:,.0f}".replace(',', '.')
    
    @app.template_filter('to_string')
    def to_string(value):
        return str(value)
    
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
