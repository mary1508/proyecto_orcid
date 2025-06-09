from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Configuración de Swagger
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Introduce tu token con el formato: Bearer {token}'
    }
}

api = Api(
    version='1.0',
    title='API de Gestión de Publicaciones Académicas',
    description='API para gestionar publicaciones académicas, proyectos y datos de investigadores',
    authorizations=authorizations,
    security='Bearer',
    doc='/api/docs'
)