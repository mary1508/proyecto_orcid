from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Publication, PublicationAuthor, Author, User
from app.extensions import db
import uuid

bp = Blueprint('publication_authors', __name__)

@bp.route('/<uuid:publication_id>/authors', methods=['GET'])
@jwt_required()
def get_publication_authors(publication_id):
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Obtener autores de la publicación
        authors = []
        for pub_author in PublicationAuthor.query.filter_by(
            publication_id=publication_id, 
            is_active=True
        ).all():
            author = Author.query.get(pub_author.author_id)
            if author:
                author_data = author.to_dict()
                author_data['order'] = pub_author.order
                author_data['is_corresponding'] = pub_author.is_corresponding
                authors.append(author_data)
        
        # Ordenar por el campo order
        authors.sort(key=lambda x: x.get('order', 0))
        
        return jsonify({
            'data': authors,
            'total': len(authors)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:publication_id>/authors', methods=['POST'])
@jwt_required()
def add_publication_author(publication_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    required_fields = ['author_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        # Verificar que la publicación existe
        publication = Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Verificar que el autor existe
        author_id = uuid.UUID(data['author_id'])
        author = Author.get_by_id(author_id)
        
        # Verificar si ya existe la relación
        existing = PublicationAuthor.query.filter_by(
            publication_id=publication_id,
            author_id=author_id,
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'error': 'El autor ya está asociado a esta publicación'}), 400
        
        # Calcular orden si no se proporciona
        if 'order' not in data:
            max_order = db.session.query(db.func.max(PublicationAuthor.order)).filter_by(
                publication_id=publication_id,
                is_active=True
            ).scalar() or 0
            data['order'] = max_order + 1
        
        # Crear la relación
        pub_author = PublicationAuthor.create(
            publication_id=publication_id,
            author_id=author_id,
            order=data.get('order', 1),
            is_corresponding=data.get('is_corresponding', False)
        )
        
        return jsonify({
            'message': 'Autor agregado a la publicación exitosamente',
            'data': {
                'publication_id': str(pub_author.publication_id),
                'author_id': str(pub_author.author_id),
                'order': pub_author.order,
                'is_corresponding': pub_author.is_corresponding,
                'author': author.to_dict()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/authors/<uuid:author_id>', methods=['PUT'])
@jwt_required()
def update_publication_author(publication_id, author_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Buscar la relación existente
        pub_author = PublicationAuthor.query.filter_by(
            publication_id=publication_id,
            author_id=author_id,
            is_active=True
        ).first()
        
        if not pub_author:
            return jsonify({'error': 'El autor no está asociado a esta publicación'}), 404
        
        # Actualizar campos
        if 'order' in data:
            pub_author.order = data['order']
        if 'is_corresponding' in data:
            pub_author.is_corresponding = data['is_corresponding']
        
        db.session.commit()
        
        # Obtener datos del autor para la respuesta
        author = Author.get_by_id(author_id)
        
        return jsonify({
            'message': 'Relación autor-publicación actualizada exitosamente',
            'data': {
                'publication_id': str(pub_author.publication_id),
                'author_id': str(pub_author.author_id),
                'order': pub_author.order,
                'is_corresponding': pub_author.is_corresponding,
                'author': author.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/authors/<uuid:author_id>', methods=['DELETE'])
@jwt_required()
def remove_publication_author(publication_id, author_id):
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Buscar la relación existente
        pub_author = PublicationAuthor.query.filter_by(
            publication_id=publication_id,
            author_id=author_id,
            is_active=True
        ).first()
        
        if not pub_author:
            return jsonify({'error': 'El autor no está asociado a esta publicación'}), 404
        
        # Desactivar en lugar de eliminar completamente
        pub_author.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Autor removido de la publicación exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/authors/reorder', methods=['PUT'])
@jwt_required()
def reorder_publication_authors(publication_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Se requiere una lista de IDs de autores en el orden deseado'}), 400
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Actualizar el orden de los autores
        for index, author_id_str in enumerate(data, start=1):
            author_id = uuid.UUID(author_id_str)
            pub_author = PublicationAuthor.query.filter_by(
                publication_id=publication_id,
                author_id=author_id,
                is_active=True
            ).first()
            
            if pub_author:
                pub_author.order = index
        
        db.session.commit()
        
        return jsonify({
            'message': 'Orden de autores actualizado exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400