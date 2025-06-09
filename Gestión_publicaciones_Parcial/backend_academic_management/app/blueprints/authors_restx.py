from flask import request, jsonify
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required
from app.extensions import db, api
from app.models import Author
from app.swagger import author_model

# Crear un namespace para los autores
ns = Namespace('authors', description='Operaciones relacionadas con autores')

# Registrar el modelo Swagger
ns.models[author_model.name] = author_model

@ns.route('/')
class AuthorList(Resource):
    @ns.doc('list_authors', security='Bearer')
    @ns.marshal_list_with(author_model)
    @jwt_required()
    def get(self):
        """Lista todos los autores"""
        authors = Author.query.all()
        return authors, 200
    
    @ns.doc('create_author', security='Bearer')
    @ns.expect(author_model)
    @ns.marshal_with(author_model, code=201)
    @jwt_required()
    def post(self):
        """Crea un nuevo autor"""
        data = request.json
        author = Author(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            affiliation=data.get('affiliation'),
            orcid_id=data.get('orcid_id')
        )
        db.session.add(author)
        db.session.commit()
        return author, 201

@ns.route('/<int:id>')
@ns.response(404, 'Autor no encontrado')
@ns.param('id', 'Identificador único del autor')
class AuthorDetail(Resource):
    @ns.doc('get_author', security='Bearer')
    @ns.marshal_with(author_model)
    @jwt_required()
    def get(self, id):
        """Obtiene detalles de un autor específico"""
        author = Author.query.get_or_404(id)
        return author
    
    @ns.doc('update_author', security='Bearer')
    @ns.expect(author_model)
    @ns.marshal_with(author_model)
    @jwt_required()
    def put(self, id):
        """Actualiza un autor existente"""
        author = Author.query.get_or_404(id)
        data = request.json
        
        # Actualizar campos
        author.first_name = data.get('first_name', author.first_name)
        author.last_name = data.get('last_name', author.last_name)
        author.email = data.get('email', author.email)
        author.affiliation = data.get('affiliation', author.affiliation)
        author.orcid_id = data.get('orcid_id', author.orcid_id)
        
        db.session.commit()
        return author
    
    @ns.doc('delete_author', security='Bearer')
    @ns.response(204, 'Autor eliminado')
    @jwt_required()
    def delete(self, id):
        """Elimina un autor"""
        author = Author.query.get_or_404(id)
        db.session.delete(author)
        db.session.commit()
        return '', 204

# Registramos el namespace en la API
api.add_namespace(ns, path='/api/authors-restx')