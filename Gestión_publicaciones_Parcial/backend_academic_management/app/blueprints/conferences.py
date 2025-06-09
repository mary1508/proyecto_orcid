from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Conference, Country
from app.extensions import db
import uuid

bp = Blueprint('conferences', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_conference():
    data = request.get_json()
    
    # Verificar campos obligatorios
    required_fields = ['name', 'year']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        conference = Conference.create(**data)
        return jsonify({
            'message': 'Conferencia creada exitosamente',
            'data': conference.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_conferences():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filtro de búsqueda por nombre
    query = Conference.query.filter_by(is_active=True)
    
    # Filtrar por país
    if request.args.get('country_id'):
        try:
            country_id = uuid.UUID(request.args.get('country_id'))
            query = query.filter_by(country_id=country_id)
        except ValueError:
            pass
    
    # Filtrar por año
    if request.args.get('year'):
        try:
            year = int(request.args.get('year'))
            query = query.filter_by(year=year)
        except ValueError:
            pass
    
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(Conference.name.ilike(search_term))
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'year')
    sort_dir = request.args.get('sort_dir', 'desc')
    
    if hasattr(Conference, sort_by):
        order_column = getattr(Conference, sort_by)
        if sort_dir.lower() == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Paginar
    paginated_query = query.paginate(page=page, per_page=per_page)
    
    # Obtener resultados con información de país
    results = []
    for item in paginated_query.items:
        conf_data = item.to_dict()
        
        # Agregar información de país si existe
        if item.country_id:
            country = Country.query.get(item.country_id)
            if country:
                conf_data['country'] = {
                    'id': str(country.id),
                    'name': country.name,
                    'code': country.code
                }
        
        results.append(conf_data)
    
    return jsonify({
        'data': results,
        'total': paginated_query.total,
        'pages': paginated_query.pages,
        'current_page': page
    })

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_conference(id):
    try:
        conference = Conference.get_by_id(id)
        conf_data = conference.to_dict()
        
        # Agregar información de país si existe
        if conference.country_id:
            country = Country.query.get(conference.country_id)
            if country:
                conf_data['country'] = {
                    'id': str(country.id),
                    'name': country.name,
                    'code': country.code
                }
        
        return jsonify(conf_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_conference(id):
    data = request.get_json()
    
    try:
        conference = Conference.update(id, **data)
        return jsonify({
            'message': 'Conferencia actualizada exitosamente',
            'data': conference.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_conference(id):
    try:
        Conference.delete(id)
        return jsonify({
            'message': 'Conferencia eliminada exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400