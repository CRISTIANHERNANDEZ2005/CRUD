from flask import Flask
from dotenv import load_dotenv
from .config import Config
from .routes import products_bp, categories_bp
from .routes.auth import auth_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object(Config)
    
    # Registrar Blueprints
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    return app