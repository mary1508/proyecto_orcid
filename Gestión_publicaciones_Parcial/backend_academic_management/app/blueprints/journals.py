from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Journal
from app.extensions import db

bp = Blueprint('journals', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_journal():
    data = request.get_json()
    
    # Verificar campos obligatorios
    required_fields = ['name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        journal = Journal.create(**data)
        return jsonify({
            'message': 'Revista creada exitosamente',
            'data': journal.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_journals():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filtro de búsqueda por nombre
    query = Journal.query.filter_by(is_active=True)
    
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(
            (Journal.name.ilike(search_term)) | 
            (Journal.issn.ilike(search_term))
        )
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc')
    
    if hasattr(Journal, sort_by):
        order_column = getattr(Journal, sort_by)
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
def get_journal(id):
    try:
        journal = Journal.get_by_id(id)
        return jsonify(journal.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_journal(id):
    data = request.get_json()
    
    try:
        journal = Journal.update(id, **data)
        return jsonify({
            'message': 'Revista actualizada exitosamente',
            'data': journal.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_journal(id):
    try:
        Journal.delete(id)
        return jsonify({
            'message': 'Revista eliminada exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400