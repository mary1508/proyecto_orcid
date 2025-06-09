from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash

bp = Blueprint('users', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query.filter_by(is_active=True).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'data': [user.to_dict() for user in query.items],
        'total': query.total,
        'pages': query.pages,
        'current_page': page
    })

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user = User.get_by_id(id)
    return jsonify(user.to_dict())

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # No permitir cambiar el password por esta ruta
    if 'password' in data:
        del data['password']
    
    try:
        user = User.update(id, **data)
        return jsonify({
            'message': 'Usuario actualizado exitosamente',
            'data': user.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>/password', methods=['PUT'])
@jwt_required()
def update_password(id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Verificar que el usuario actual sea el mismo o un administrador
    if str(id) != current_user_id:
        current_user = User.query.filter_by(id=current_user_id).first()
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'No autorizado para realizar esta acción'}), 403
    
    if not data.get('password'):
        return jsonify({'error': 'La contraseña es obligatoria'}), 400
    
    try:
        user = User.get_by_id(id)
        user.password_hash = generate_password_hash(data['password'])
        db.session.commit()
        
        return jsonify({
            'message': 'Contraseña actualizada exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    current_user_id = get_jwt_identity()
    
    # Verificar que el usuario actual sea el mismo o un administrador
    if str(id) != current_user_id:
        current_user = User.query.filter_by(id=current_user_id).first()
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'No autorizado para realizar esta acción'}), 403
    
    try:
        User.delete(id)
        return jsonify({
            'message': 'Usuario eliminado exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400