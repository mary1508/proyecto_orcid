import json
import os
import sys

# Añadimos el directorio raíz del proyecto al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import api

def export_swagger():
    """Exporta la documentación Swagger a un archivo JSON"""
    # Creamos la aplicación
    app = create_app()
    
    # Añadimos las configuraciones necesarias para generar URLs correctamente
    app.config['SERVER_NAME'] = 'localhost:5000'
    app.config['APPLICATION_ROOT'] = '/'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    # Creamos el contexto de la aplicación
    with app.app_context():
        # Obtenemos la especificación Swagger
        swagger_spec = api.__schema__
        
        # Aseguramos que la carpeta docs exista
        os.makedirs('docs', exist_ok=True)
        
        # Guardamos la especificación en un archivo JSON
        with open('docs/openapi.json', 'w') as f:
            json.dump(swagger_spec, f, indent=2)
        
        print("Documentación Swagger exportada exitosamente a docs/openapi.json")
        
        # También podríamos guardarla en formato YAML si lo preferimos
        try:
            import yaml
            with open('docs/openapi.yaml', 'w') as f:
                yaml.dump(swagger_spec, f, sort_keys=False)
            print("Documentación Swagger exportada exitosamente a docs/openapi.yaml")
        except ImportError:
            print("Para exportar en formato YAML, instala PyYAML: pip install pyyaml")

if __name__ == '__main__':
    export_swagger()