from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    get_jwt_identity, jwt_required
)
from app.models import RefreshToken, User
from app.extensions import db
import datetime
import uuid

bp = Blueprint('refresh_tokens', __name__)

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Endpoint para renovar el token de acceso usando un token de refresco.
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que el usuario existe
        user = User.query.get(uuid.UUID(current_user_id))
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Verificar que el token de refresco es válido y activo
        refresh_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        token_record = RefreshToken.query.filter_by(
            token=refresh_token,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not token_record:
            return jsonify({'error': 'Token de refresco inválido o expirado'}), 401
        
        # Verificar si el token ha expirado
        if token_record.expires_at and token_record.expires_at < datetime.datetime.utcnow():
            token_record.is_active = False
            db.session.commit()
            return jsonify({'error': 'Token de refresco expirado'}), 401
        
        # Generar nuevo token de acceso
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict(exclude=['password'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Endpoint para invalidar todos los tokens de refresco del usuario actual.
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Desactivar todos los tokens de refresco del usuario
        RefreshToken.query.filter_by(
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).update({
            'is_active': False
        })
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sesión cerrada exitosamente. Todos los tokens han sido invalidados.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/revoke/<uuid:token_id>', methods=['POST'])
@jwt_required()
def revoke_token(token_id):
    """
    Endpoint para revocar un token de refresco específico.
    Sólo el propietario del token o un administrador puede revocarlo.
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Buscar el token
        token = RefreshToken.query.get(token_id)
        
        if not token:
            return jsonify({'error': 'Token no encontrado'}), 404
        
        # Verificar que el usuario actual es el propietario del token o un administrador
        if str(token.user_id) != current_user_id:
            # Aquí podrías agregar verificación adicional para administradores
            return jsonify({'error': 'No tienes permisos para revocar este token'}), 403
        
        # Revocar el token
        token.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Token revocado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_tokens():
    """
    Endpoint para obtener todos los tokens de refresco activos del usuario actual.
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener todos los tokens activos del usuario
        tokens = RefreshToken.query.filter_by(
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).all()
        
        result = []
        for token in tokens:
            result.append({
                'id': str(token.id),
                'user_agent': token.user_agent,
                'ip_address': token.ip_address,
                'created_at': token.created_at.isoformat() if token.created_at else None,
                'expires_at': token.expires_at.isoformat() if token.expires_at else None,
                'last_used_at': token.last_used_at.isoformat() if token.last_used_at else None
            })
        
        return jsonify({
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400