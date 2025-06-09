from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Publication, PublicationKeyword, Keyword
from app.extensions import db
import uuid

bp = Blueprint('publication_keywords', __name__)

@bp.route('/<uuid:publication_id>/keywords', methods=['GET'])
@jwt_required()
def get_publication_keywords(publication_id):
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Obtener palabras clave de la publicación
        keywords = []
        for pub_keyword in PublicationKeyword.query.filter_by(
            publication_id=publication_id, 
            is_active=True
        ).all():
            keyword = Keyword.query.get(pub_keyword.keyword_id)
            if keyword:
                keywords.append(keyword.to_dict())
        
        return jsonify({
            'data': keywords,
            'total': len(keywords)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:publication_id>/keywords', methods=['POST'])
@jwt_required()
def add_publication_keyword(publication_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    if not data.get('keyword_id') and not data.get('keyword_text'):
        return jsonify({'error': 'Se requiere keyword_id o keyword_text'}), 400
    
    try:
        # Verificar que la publicación existe
        publication = Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        keyword_id = None
        
        # Si se proporciona un ID de palabra clave existente
        if data.get('keyword_id'):
            keyword_id = uuid.UUID(data['keyword_id'])
            keyword = Keyword.get_by_id(keyword_id)
        # Si se proporciona texto para crear una nueva palabra clave
        elif data.get('keyword_text'):
            # Buscar si ya existe una palabra clave con ese texto
            existing_keyword = Keyword.query.filter_by(
                text=data['keyword_text'], 
                is_active=True
            ).first()
            
            if existing_keyword:
                keyword = existing_keyword
                keyword_id = existing_keyword.id
            else:
                # Crear nueva palabra clave
                keyword = Keyword.create(text=data['keyword_text'])
                keyword_id = keyword.id
        
        # Verificar si ya existe la relación
        existing = PublicationKeyword.query.filter_by(
            publication_id=publication_id,
            keyword_id=keyword_id,
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'error': 'Esta palabra clave ya está asociada a la publicación'}), 400
        
        # Crear la relación
        pub_keyword = PublicationKeyword.create(
            publication_id=publication_id,
            keyword_id=keyword_id
        )
        
        return jsonify({
            'message': 'Palabra clave agregada a la publicación exitosamente',
            'data': {
                'publication_id': str(pub_keyword.publication_id),
                'keyword_id': str(pub_keyword.keyword_id),
                'keyword': keyword.to_dict()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/keywords/<uuid:keyword_id>', methods=['DELETE'])
@jwt_required()
def remove_publication_keyword(publication_id, keyword_id):
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Buscar la relación existente
        pub_keyword = PublicationKeyword.query.filter_by(
            publication_id=publication_id,
            keyword_id=keyword_id,
            is_active=True
        ).first()
        
        if not pub_keyword:
            return jsonify({'error': 'Esta palabra clave no está asociada a la publicación'}), 404
        
        # Desactivar en lugar de eliminar completamente
        pub_keyword.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Palabra clave removida de la publicación exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/keywords/batch', methods=['POST'])
@jwt_required()
def batch_add_publication_keywords(publication_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    if not isinstance(data, list):
        return jsonify({'error': 'Se requiere una lista de palabras clave'}), 400
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        results = []
        
        for keyword_data in data:
            keyword_id = None
            
            # Si se proporciona un ID de palabra clave existente
            if keyword_data.get('keyword_id'):
                keyword_id = uuid.UUID(keyword_data['keyword_id'])
                keyword = Keyword.get_by_id(keyword_id)
            # Si se proporciona texto para crear una nueva palabra clave
            elif keyword_data.get('keyword_text'):
                # Buscar si ya existe una palabra clave con ese texto
                existing_keyword = Keyword.query.filter_by(
                    text=keyword_data['keyword_text'], 
                    is_active=True
                ).first()
                
                if existing_keyword:
                    keyword = existing_keyword
                    keyword_id = existing_keyword.id
                else:
                    # Crear nueva palabra clave
                    keyword = Keyword.create(text=keyword_data['keyword_text'])
                    keyword_id = keyword.id
            else:
                # Si no hay ID ni texto, omitir este elemento
                continue
            
            # Verificar si ya existe la relación
            existing = PublicationKeyword.query.filter_by(
                publication_id=publication_id,
                keyword_id=keyword_id,
                is_active=True
            ).first()
            
            if not existing:
                # Crear la relación
                pub_keyword = PublicationKeyword.create(
                    publication_id=publication_id,
                    keyword_id=keyword_id
                )
                
                results.append({
                    'publication_id': str(pub_keyword.publication_id),
                    'keyword_id': str(pub_keyword.keyword_id),
                    'keyword': keyword.to_dict()
                })
        
        return jsonify({
            'message': f'{len(results)} palabras clave agregadas a la publicación exitosamente',
            'data': results
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400