from app import create_app

app = create_app()

app.config['TEMPLATES_AUTO_RELOAD'] = True  # Ensures templates are reloaded
app.jinja_env.auto_reload = True  # Jinja2 autoreload
    
if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
