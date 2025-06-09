from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Keyword, PublicationKeyword, Publication
from app.extensions import db

bp = Blueprint('keywords', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_keyword():
    data = request.get_json()
    
    # Verificar campos obligatorios
    if 'name' not in data:
        return jsonify({'error': 'Campo name es obligatorio'}), 400
    
    try:
        # Verificar si ya existe la keyword
        existing = Keyword.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'message': 'La palabra clave ya existe',
                'data': existing.to_dict()
            }), 200
        
        keyword = Keyword.create(**data)
        return jsonify({
            'message': 'Palabra clave creada exitosamente',
            'data': keyword.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_keywords():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtro de búsqueda por nombre
    query = Keyword.query.filter_by(is_active=True)
    
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(Keyword.name.ilike(search_term))
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc')
    
    if hasattr(Keyword, sort_by):
        order_column = getattr(Keyword, sort_by)
        if sort_dir.lower() == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Paginar
    paginated_query = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'data': [item.to_dict() for item in paginated_query.items],
        'total': paginated_query.total,
        'pages': paginated_query.pages,
        'current_page': page
    })

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_keyword(id):
    try:
        keyword = Keyword.get_by_id(id)
        keyword_data = keyword.to_dict()
        
        # Obtener publicaciones relacionadas
        publications = []
        pub_keywords = PublicationKeyword.query.filter_by(keyword_id=id).all()
        
        for pub_keyword in pub_keywords:
            publication = Publication.query.filter_by(id=pub_keyword.publication_id, is_active=True).first()
            if publication:
                publications.append({
                    'id': str(publication.id),
                    'title': publication.title,
                    'publication_date': publication.publication_date.isoformat() if publication.publication_date else None,
                    'doi': publication.doi
                })
        
        keyword_data['publications'] = publications
        
        return jsonify(keyword_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_keyword(id):
    data = request.get_json()
    
    try:
        keyword = Keyword.update(id, **data)
        return jsonify({
            'message': 'Palabra clave actualizada exitosamente',
            'data': keyword.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_keyword(id):
    try:
        # Verificar si hay publicaciones usando esta keyword
        if PublicationKeyword.query.filter_by(keyword_id=id).first():
            return jsonify({
                'error': 'No se puede eliminar esta palabra clave porque está en uso por publicaciones'
            }), 400
        
        Keyword.delete(id)
        return jsonify({
            'message': 'Palabra clave eliminada exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400