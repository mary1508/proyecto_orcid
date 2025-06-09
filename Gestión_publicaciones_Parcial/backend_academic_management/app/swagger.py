from flask_restx import Api, Resource, fields, Namespace
from .extensions import api
from flask import Blueprint

# Creamos un Blueprint para Swagger
swagger_bp = Blueprint('swagger', __name__)

# Definición de namespaces para cada sección de la API
authors_ns = api.namespace('Autores', description='Operaciones relacionadas con autores', path='/api/authors')
publications_ns = api.namespace('Publicaciones', description='Operaciones relacionadas con publicaciones', path='/api/publications')
journals_ns = api.namespace('Revistas', description='Operaciones relacionadas con revistas académicas', path='/api/journals')
conferences_ns = api.namespace('Conferencias', description='Operaciones relacionadas con conferencias', path='/api/conferences')
projects_ns = api.namespace('Proyectos', description='Operaciones relacionadas con proyectos de investigación', path='/api/projects')
keywords_ns = api.namespace('Palabras clave', description='Operaciones relacionadas con palabras clave', path='/api/keywords')
countries_ns = api.namespace('Países', description='Operaciones relacionadas con países', path='/api/countries')
users_ns = api.namespace('Usuarios', description='Operaciones relacionadas con usuarios del sistema', path='/api/users')
orcid_ns = api.namespace('ORCID', description='Operaciones relacionadas con la integración de ORCID', path='/api/orcid')

# Modelos para la documentación
# Modelo de Autor
author_model = api.model('Autor', {
    'id': fields.Integer(readonly=True, description='Identificador único del autor'),
    'first_name': fields.String(required=True, description='Nombre del autor'),
    'last_name': fields.String(required=True, description='Apellido del autor'),
    'orcid_id': fields.String(description='Identificador ORCID del autor'),
    'email': fields.String(description='Correo electrónico del autor'),
    'affiliation': fields.String(description='Afiliación institucional del autor')
})

# Modelo de Usuario
user_model = api.model('Usuario', {
    'id': fields.Integer(readonly=True, description='Identificador único del usuario'),
    'username': fields.String(required=True, description='Nombre de usuario'),
    'email': fields.String(required=True, description='Correo electrónico del usuario'),
    'first_name': fields.String(description='Nombre del usuario'),
    'last_name': fields.String(description='Apellido del usuario'),
    'is_active': fields.Boolean(description='Indica si el usuario está activo')
})

# Modelo de País
country_model = api.model('País', {
    'id': fields.Integer(readonly=True, description='Identificador único del país'),
    'name': fields.String(required=True, description='Nombre del país'),
    'code': fields.String(required=True, description='Código ISO del país')
})

# Modelo de Palabra Clave
keyword_model = api.model('Palabra Clave', {
    'id': fields.Integer(readonly=True, description='Identificador único de la palabra clave'),
    'name': fields.String(required=True, description='Nombre de la palabra clave')
})

# Modelo de Revista
journal_model = api.model('Revista', {
    'id': fields.Integer(readonly=True, description='Identificador único de la revista'),
    'name': fields.String(required=True, description='Nombre de la revista'),
    'country_id': fields.Integer(required=True, description='ID del país de la revista'),
    'quartile': fields.Integer(description='Cuartil de la revista (1-4)'),
    'h_index': fields.Integer(description='Índice H de la revista'),
    'description': fields.String(description='Descripción de la revista')
})

# Modelo de Conferencia
conference_model = api.model('Conferencia', {
    'id': fields.Integer(readonly=True, description='Identificador único de la conferencia'),
    'name': fields.String(required=True, description='Nombre de la conferencia'),
    'year': fields.Integer(required=True, description='Año de la conferencia'),
    'country_id': fields.Integer(required=True, description='ID del país de la conferencia'),
    'place': fields.String(description='Lugar de la conferencia'),
    'description': fields.String(description='Descripción de la conferencia')
})

# Modelo de Tipo de Publicación
publication_type_model = api.model('Tipo de Publicación', {
    'id': fields.Integer(readonly=True, description='Identificador único del tipo de publicación'),
    'name': fields.String(required=True, description='Nombre del tipo de publicación')
})

# Modelo de Publicación
publication_model = api.model('Publicación', {
    'id': fields.Integer(readonly=True, description='Identificador único de la publicación'),
    'title': fields.String(required=True, description='Título de la publicación'),
    'abstract': fields.String(description='Resumen de la publicación'),
    'year': fields.Integer(description='Año de publicación'),
    'month': fields.Integer(description='Mes de publicación'),
    'day': fields.Integer(description='Día de publicación'),
    'doi': fields.String(description='DOI de la publicación'),
    'url': fields.String(description='URL de la publicación'),
    'publication_type_id': fields.Integer(required=True, description='ID del tipo de publicación'),
    'journal_id': fields.Integer(description='ID de la revista (si aplica)'),
    'conference_id': fields.Integer(description='ID de la conferencia (si aplica)'),
    'pdf_path': fields.String(description='Ruta al documento PDF'),
    'external_id': fields.String(description='Identificador externo de la publicación')
})

# Modelo de Proyecto
project_model = api.model('Proyecto', {
    'id': fields.Integer(readonly=True, description='Identificador único del proyecto'),
    'name': fields.String(required=True, description='Nombre del proyecto'),
    'description': fields.String(description='Descripción del proyecto'),
    'start_date': fields.Date(description='Fecha de inicio del proyecto'),
    'end_date': fields.Date(description='Fecha de fin del proyecto'),
    'budget': fields.Float(description='Presupuesto del proyecto')
})

# Modelo de Miembro de Proyecto
project_member_model = api.model('Miembro de Proyecto', {
    'id': fields.Integer(readonly=True, description='Identificador único del miembro del proyecto'),
    'project_id': fields.Integer(required=True, description='ID del proyecto'),
    'author_id': fields.Integer(required=True, description='ID del autor'),
    'role': fields.String(description='Rol en el proyecto')
})

# Modelo de Hito
milestone_model = api.model('Hito', {
    'id': fields.Integer(readonly=True, description='Identificador único del hito'),
    'project_id': fields.Integer(required=True, description='ID del proyecto'),
    'name': fields.String(required=True, description='Nombre del hito'),
    'description': fields.String(description='Descripción del hito'),
    'due_date': fields.Date(description='Fecha de entrega del hito'),
    'status': fields.String(description='Estado del hito')
})

# Modelo de Entregable
deliverable_model = api.model('Entregable', {
    'id': fields.Integer(readonly=True, description='Identificador único del entregable'),
    'milestone_id': fields.Integer(required=True, description='ID del hito asociado'),
    'name': fields.String(required=True, description='Nombre del entregable'),
    'description': fields.String(description='Descripción del entregable'),
    'file_path': fields.String(description='Ruta al archivo del entregable')
})

# Modelo de Adquisición
acquisition_model = api.model('Adquisición', {
    'id': fields.Integer(readonly=True, description='Identificador único de la adquisición'),
    'project_id': fields.Integer(required=True, description='ID del proyecto'),
    'name': fields.String(required=True, description='Nombre del producto/servicio adquirido'),
    'description': fields.String(description='Descripción de la adquisición'),
    'amount': fields.Float(description='Monto de la adquisición'),
    'acquisition_date': fields.Date(description='Fecha de adquisición')
})

# Modelo de Referencia de Publicación
publication_reference_model = api.model('Referencia de Publicación', {
    'id': fields.Integer(readonly=True, description='Identificador único de la referencia'),
    'publication_id': fields.Integer(required=True, description='ID de la publicación que contiene la referencia'),
    'reference_id': fields.Integer(description='ID de la publicación referenciada'),
    'citation_text': fields.String(description='Texto de la cita')
})

# Modelo de Publicación-Autor
publication_author_model = api.model('Publicación-Autor', {
    'id': fields.Integer(readonly=True, description='Identificador único de la relación'),
    'publication_id': fields.Integer(required=True, description='ID de la publicación'),
    'author_id': fields.Integer(required=True, description='ID del autor'),
    'is_corresponding': fields.Boolean(description='Indica si es autor correspondiente')
})

# Modelo de Publicación-Palabra Clave
publication_keyword_model = api.model('Publicación-Palabra Clave', {
    'id': fields.Integer(readonly=True, description='Identificador único de la relación'),
    'publication_id': fields.Integer(required=True, description='ID de la publicación'),
    'keyword_id': fields.Integer(required=True, description='ID de la palabra clave')
})

# Modelo de Token de Autenticación
auth_model = api.model('Autenticación', {
    'username': fields.String(required=True, description='Nombre de usuario'),
    'password': fields.String(required=True, description='Contraseña')
})

token_model = api.model('Token', {
    'access_token': fields.String(description='Token de acceso JWT'),
    'refresh_token': fields.String(description='Token de refresco JWT')
})

# Modelo para ORCID
orcid_researcher_model = api.model('Investigador ORCID', {
    'orcid_id': fields.String(required=True, description='Identificador ORCID del investigador'),
    'first_name': fields.String(description='Nombre del investigador'),
    'last_name': fields.String(description='Apellido del investigador'),
    'credit_name': fields.String(description='Nombre de crédito del investigador'),
    'email': fields.String(description='Correo electrónico del investigador'),
    'affiliation': fields.String(description='Afiliación del investigador')
})

orcid_work_model = api.model('Publicación ORCID', {
    'title': fields.String(description='Título de la publicación'),
    'type': fields.String(description='Tipo de publicación'),
    'year': fields.Integer(description='Año de publicación'),
    'journal': fields.String(description='Revista o fuente de publicación'),
    'external_id': fields.String(description='Identificador externo'),
    'doi': fields.String(description='DOI de la publicación'),
    'url': fields.String(description='URL de la publicación')
})
# Modelo para lista de trabajos ORCID
orcid_works_response_model = api.model('OrcidWorksResponse', {
    'data': fields.List(fields.Nested(orcid_work_model), description='Lista de publicaciones del investigador')
})

# Definición de ejemplos de respuestas de endpoints
@authors_ns.route('/')
class AuthorsList(Resource):
    @api.doc('listar_autores', security='Bearer')
    @api.response(200, 'Operación exitosa', [author_model])
    @api.response(401, 'No autorizado')
    def get(self):
        """Lista todos los autores"""
        pass
        
    @api.doc('crear_autor', security='Bearer')
    @api.expect(author_model)
    @api.response(201, 'Autor creado exitosamente')
    @api.response(400, 'Datos inválidos')
    @api.response(401, 'No autorizado')
    def post(self):
        """Crea un nuevo autor"""
        pass

@authors_ns.route('/<int:id>')
@api.doc(params={'id': 'Identificador del autor'})
class AuthorDetail(Resource):
    @api.doc('obtener_autor', security='Bearer')
    @api.response(200, 'Operación exitosa', author_model)
    @api.response(404, 'Autor no encontrado')
    @api.response(401, 'No autorizado')
    def get(self, id):
        """Obtiene un autor por su ID"""
        pass
        
    @api.doc('actualizar_autor', security='Bearer')
    @api.expect(author_model)
    @api.response(200, 'Autor actualizado exitosamente')
    @api.response(400, 'Datos inválidos')
    @api.response(404, 'Autor no encontrado')
    @api.response(401, 'No autorizado')
    def put(self, id):
        """Actualiza un autor existente"""
        pass
        
    @api.doc('eliminar_autor', security='Bearer')
    @api.response(204, 'Autor eliminado exitosamente')
    @api.response(404, 'Autor no encontrado')
    @api.response(401, 'No autorizado')
    def delete(self, id):
        """Elimina un autor"""
        pass

@publications_ns.route('/')
class PublicationsList(Resource):
    @api.doc('listar_publicaciones', security='Bearer')
    @api.response(200, 'Operación exitosa', [publication_model])
    @api.response(401, 'No autorizado')
    def get(self):
        """Lista todas las publicaciones"""
        pass
        
    @api.doc('crear_publicacion', security='Bearer')
    @api.expect(publication_model)
    @api.response(201, 'Publicación creada exitosamente')
    @api.response(400, 'Datos inválidos')
    @api.response(401, 'No autorizado')
    def post(self):
        """Crea una nueva publicación"""
        pass

@orcid_ns.route('/sync/<string:orcid_id>')
@api.doc(params={'orcid_id': 'Identificador ORCID del investigador'})
class OrcidSync(Resource):
    @api.doc('sincronizar_investigador', security='Bearer')
    @api.response(200, 'Sincronización exitosa')
    @api.response(404, 'Investigador no encontrado')
    @api.response(401, 'No autorizado')
    def post(self, orcid_id):
        """Sincroniza datos de un investigador desde ORCID"""
        pass

@orcid_ns.route('/researcher/<string:orcid_id>')
@api.doc(params={'orcid_id': 'Identificador ORCID del investigador'})
class OrcidResearcher(Resource):
    @api.doc('obtener_investigador', security='Bearer')
    @api.response(200, 'Operación exitosa', orcid_researcher_model)
    @api.response(404, 'Investigador no encontrado')
    @api.response(401, 'No autorizado')
    def get(self, orcid_id):
        """Obtiene información básica de un investigador por su ORCID ID"""
        pass

@orcid_ns.route('/researcher/<string:orcid_id>/works')
@api.doc(params={'orcid_id': 'Identificador ORCID del investigador'})
class OrcidWorks(Resource):
    @api.doc('obtener_publicaciones', security='Bearer')
    @api.response(200, 'Operación exitosa', orcid_works_response_model)  # Usar el nuevo modelo aquí
    @api.response(404, 'Publicaciones no encontradas')
    @api.response(401, 'No autorizado')
    def get(self, orcid_id):
        """Obtiene las publicaciones de un investigador por su ORCID ID"""
        pass

def configure_swagger(app):
    """Configura Swagger en la aplicación Flask"""
    api.init_app(app)