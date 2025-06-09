from .config import Config
from .extensions import db, migrate, jwt
from .blueprints import register_blueprints
from .swagger import configure_swagger
from flask import Flask
from flask_cors import CORS
def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    CORS(app, supports_credentials=True)

    app.config.from_object(Config)


    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Inicializar JWT
    jwt.init_app(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Configurar Swagger
    configure_swagger(app)
    
    return app