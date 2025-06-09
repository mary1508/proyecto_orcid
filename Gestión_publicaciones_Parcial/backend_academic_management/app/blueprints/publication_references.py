from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Publication, PublicationReference
from app.extensions import db
import uuid

bp = Blueprint('publication_references', __name__)

@bp.route('/<uuid:publication_id>/references', methods=['GET'])
@jwt_required()
def get_publication_references(publication_id):
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Obtener referencias de la publicación
        references = []
        for pub_ref in PublicationReference.query.filter_by(
            publication_id=publication_id, 
            is_active=True
        ).order_by(PublicationReference.order).all():
            reference_data = {
                'id': str(pub_ref.id),
                'publication_id': str(pub_ref.publication_id),
                'reference_text': pub_ref.reference_text,
                'order': pub_ref.order,
                'doi': pub_ref.doi,
                'url': pub_ref.url,
                'created_at': pub_ref.created_at.isoformat() if pub_ref.created_at else None
            }
            
            # Si hay una publicación referenciada, agregar sus datos
            if pub_ref.reference_publication_id:
                ref_publication = Publication.query.get(pub_ref.reference_publication_id)
                if ref_publication:
                    reference_data['reference_publication'] = ref_publication.to_dict()
            
            references.append(reference_data)
        
        return jsonify({
            'data': references,
            'total': len(references)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:publication_id>/references', methods=['POST'])
@jwt_required()
def add_publication_reference(publication_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    if not data.get('reference_text') and not data.get('reference_publication_id'):
        return jsonify({'error': 'Se requiere reference_text o reference_publication_id'}), 400
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Calcular orden si no se proporciona
        if 'order' not in data:
            max_order = db.session.query(db.func.max(PublicationReference.order)).filter_by(
                publication_id=publication_id,
                is_active=True
            ).scalar() or 0
            data['order'] = max_order + 1
        
        # Si se proporciona un ID de publicación como referencia
        if data.get('reference_publication_id'):
            reference_publication_id = uuid.UUID(data['reference_publication_id'])
            # Verificar que la publicación referenciada existe
            reference_publication = Publication.get_by_id(reference_publication_id)
            
            # Evitar auto-referencia
            if reference_publication_id == publication_id:
                return jsonify({'error': 'Una publicación no puede referenciarse a sí misma'}), 400
            
            # Crear referencia
            pub_ref = PublicationReference.create(
                publication_id=publication_id,
                reference_publication_id=reference_publication_id,
                reference_text=data.get('reference_text', f"{reference_publication.title} ({reference_publication.year})"),
                order=data.get('order', 1),
                doi=data.get('doi', reference_publication.doi),
                url=data.get('url', reference_publication.url)
            )
        # Si solo se proporciona texto de referencia
        else:
            pub_ref = PublicationReference.create(
                publication_id=publication_id,
                reference_text=data['reference_text'],
                order=data.get('order', 1),
                doi=data.get('doi'),
                url=data.get('url')
            )
        
        return jsonify({
            'message': 'Referencia agregada a la publicación exitosamente',
            'data': {
                'id': str(pub_ref.id),
                'publication_id': str(pub_ref.publication_id),
                'reference_publication_id': str(pub_ref.reference_publication_id) if pub_ref.reference_publication_id else None,
                'reference_text': pub_ref.reference_text,
                'order': pub_ref.order,
                'doi': pub_ref.doi,
                'url': pub_ref.url
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/references/<uuid:reference_id>', methods=['PUT'])
@jwt_required()
def update_publication_reference(publication_id, reference_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Buscar la referencia existente
        pub_ref = PublicationReference.query.filter_by(
            id=reference_id,
            publication_id=publication_id,
            is_active=True
        ).first()
        
        if not pub_ref:
            return jsonify({'error': 'La referencia no existe para esta publicación'}), 404
        
        # Actualizar campos
        if 'reference_text' in data:
            pub_ref.reference_text = data['reference_text']
        if 'order' in data:
            pub_ref.order = data['order']
        if 'doi' in data:
            pub_ref.doi = data['doi']
        if 'url' in data:
            pub_ref.url = data['url']
        if 'reference_publication_id' in data:
            if data['reference_publication_id']:
                reference_publication_id = uuid.UUID(data['reference_publication_id'])
                # Verificar que la publicación referenciada existe
                reference_publication = Publication.get_by_id(reference_publication_id)
                
                # Evitar auto-referencia
                if reference_publication_id == publication_id:
                    return jsonify({'error': 'Una publicación no puede referenciarse a sí misma'}), 400
                
                pub_ref.reference_publication_id = reference_publication_id
            else:
                pub_ref.reference_publication_id = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Referencia actualizada exitosamente',
            'data': {
                'id': str(pub_ref.id),
                'publication_id': str(pub_ref.publication_id),
                'reference_publication_id': str(pub_ref.reference_publication_id) if pub_ref.reference_publication_id else None,
                'reference_text': pub_ref.reference_text,
                'order': pub_ref.order,
                'doi': pub_ref.doi,
                'url': pub_ref.url
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/references/<uuid:reference_id>', methods=['DELETE'])
@jwt_required()
def remove_publication_reference(publication_id, reference_id):
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Buscar la referencia existente
        pub_ref = PublicationReference.query.filter_by(
            id=reference_id,
            publication_id=publication_id,
            is_active=True
        ).first()
        
        if not pub_ref:
            return jsonify({'error': 'La referencia no existe para esta publicación'}), 404
        
        # Desactivar en lugar de eliminar completamente
        pub_ref.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Referencia eliminada exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:publication_id>/references/reorder', methods=['PUT'])
@jwt_required()
def reorder_publication_references(publication_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Se requiere una lista de IDs de referencias en el orden deseado'}), 400
    
    try:
        # Verificar que la publicación existe
        Publication.get_by_id(publication_id)
        
        # Verificar que el usuario actual tiene permisos para editar la publicación
        # (esto dependerá de tu lógica de negocio)
        
        # Actualizar el orden de las referencias
        for index, reference_id_str in enumerate(data, start=1):
            reference_id = uuid.UUID(reference_id_str)
            pub_ref = PublicationReference.query.filter_by(
                id=reference_id,
                publication_id=publication_id,
                is_active=True
            ).first()
            
            if pub_ref:
                pub_ref.order = index
        
        db.session.commit()
        
        return jsonify({
            'message': 'Orden de referencias actualizado exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400