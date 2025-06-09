from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, RefreshToken
from app.extensions import db
from datetime import datetime, timedelta
import uuid

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Verificar datos necesarios
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    # Verificar si el usuario ya existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Nombre de usuario ya está en uso'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Correo electrónico ya está en uso'}), 400
    
    # Crear nuevo usuario
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        role=data.get('role', 'user'),
        orcid_id=data.get('orcid_id')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'Usuario registrado exitosamente',
        'user': {
            'id': str(new_user.id),
            'username': new_user.username,
            'email': new_user.email,
            'role': new_user.role
        }
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Verificar datos necesarios
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Se requieren nombre de usuario y contraseña'}), 400
    
    # Buscar usuario
    user = User.query.filter_by(username=data['username']).first()
    
    # Verificar si el usuario existe y la contraseña es correcta
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Crear tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # Guardar refresh token en la base de datos
    expires_at = datetime.utcnow() + timedelta(days=30)
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    db.session.add(db_refresh_token)
    db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    
    # Verificar si el usuario existe
    user = User.query.filter_by(id=uuid.UUID(current_user_id)).first()
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Crear nuevo access token
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': access_token
    }), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_info():
    current_user_id = get_jwt_identity()
    
    # Verificar si el usuario existe
    user = User.query.filter_by(id=uuid.UUID(current_user_id)).first()
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'orcid_id': user.orcid_id,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    }), 200