from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Country
from app.extensions import db

bp = Blueprint('countries', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_country():
    data = request.get_json()
    
    # Verificar campos obligatorios
    required_fields = ['name', 'code']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        country = Country.create(**data)
        return jsonify({
            'message': 'País creado exitosamente',
            'data': country.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_countries():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtro de búsqueda por nombre
    query = Country.query.filter_by(is_active=True)
    
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(Country.name.ilike(search_term) | Country.code.ilike(search_term))
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc')
    
    if hasattr(Country, sort_by):
        order_column = getattr(Country, sort_by)
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
def get_country(id):
    try:
        country = Country.get_by_id(id)
        return jsonify(country.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_country(id):
    data = request.get_json()
    
    try:
        country = Country.update(id, **data)
        return jsonify({
            'message': 'País actualizado exitosamente',
            'data': country.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_country(id):
    try:
        Country.delete(id)
        return jsonify({
            'message': 'País eliminado exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400