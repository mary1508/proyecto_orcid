from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import ProjectMember, Project, User
from app.extensions import db
import uuid

bp = Blueprint('project_members', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_project_member():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    required_fields = ['project_id', 'user_id', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        # Verificar que el usuario actual tiene permisos en el proyecto
        project_id = uuid.UUID(data['project_id'])
        current_member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not current_member or current_member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para añadir miembros a este proyecto'}), 403
        
        # Verificar si el usuario a agregar ya es miembro
        user_id = uuid.UUID(data['user_id'])
        existing_member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        
        if existing_member:
            if existing_member.is_active:
                return jsonify({'error': 'El usuario ya es miembro activo del proyecto'}), 400
            else:
                # Reactivar miembro
                existing_member.is_active = True
                existing_member.role = data['role']
                db.session.commit()
                
                return jsonify({
                    'message': 'Miembro reactivado exitosamente',
                    'data': {
                        'project_id': str(existing_member.project_id),
                        'user_id': str(existing_member.user_id),
                        'role': existing_member.role,
                        'is_active': existing_member.is_active
                    }
                }), 200
        
        # Crear nuevo miembro
        new_member = ProjectMember.create(
            project_id=project_id,
            user_id=user_id,
            role=data['role'],
            is_active=True
        )
        
        return jsonify({
            'message': 'Miembro añadido al proyecto exitosamente',
            'data': {
                'project_id': str(new_member.project_id),
                'user_id': str(new_member.user_id),
                'role': new_member.role,
                'is_active': new_member.is_active
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_project_members():
    current_user_id = get_jwt_identity()
    project_id = request.args.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Se requiere el ID del proyecto'}), 400
    
    try:
        project_id = uuid.UUID(project_id)
        
        # Verificar que el usuario tenga acceso al proyecto
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        # Obtener miembros
        members_query = ProjectMember.query.filter_by(
            project_id=project_id,
            is_active=True
        )
        
        members = []
        for member in members_query.all():
            user = User.query.get(member.user_id)
            if user:
                members.append({
                    'id': str(member.id),
                    'user_id': str(member.user_id),
                    'project_id': str(member.project_id),
                    'role': member.role,
                    'created_at': member.created_at.isoformat() if member.created_at else None,
                    'updated_at': member.updated_at.isoformat() if member.updated_at else None,
                    'user': {
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                })
        
        return jsonify({
            'data': members,
            'total': len(members)
        })
    except ValueError:
        return jsonify({'error': 'ID de proyecto inválido'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_project_member(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener miembro del proyecto
        member = ProjectMember.query.filter_by(id=id, is_active=True).first()
        
        if not member:
            return jsonify({'error': 'Miembro del proyecto no encontrado'}), 404
        
        # Verificar que el usuario actual tiene acceso al proyecto
        user_is_member = ProjectMember.query.filter_by(
            project_id=member.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not user_is_member:
            return jsonify({'error': 'No tienes acceso a este proyecto'}), 403
        
        # Obtener usuario asociado
        user = User.query.get(member.user_id)
        
        return jsonify({
            'id': str(member.id),
            'user_id': str(member.user_id),
            'project_id': str(member.project_id),
            'role': member.role,
            'created_at': member.created_at.isoformat() if member.created_at else None,
            'updated_at': member.updated_at.isoformat() if member.updated_at else None,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            } if user else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_project_member(id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener miembro del proyecto
        member = ProjectMember.query.filter_by(id=id).first()
        
        if not member:
            return jsonify({'error': 'Miembro del proyecto no encontrado'}), 404
        
        # Verificar que el usuario actual es líder del proyecto
        current_member = ProjectMember.query.filter_by(
            project_id=member.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not current_member or current_member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para modificar miembros de este proyecto'}), 403
        
        # Actualizar campos
        if 'role' in data:
            member.role = data['role']
        if 'is_active' in data:
            member.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Miembro del proyecto actualizado exitosamente',
            'data': {
                'id': str(member.id),
                'user_id': str(member.user_id),
                'project_id': str(member.project_id),
                'role': member.role,
                'is_active': member.is_active
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_project_member(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener miembro del proyecto
        member = ProjectMember.query.filter_by(id=id).first()
        
        if not member:
            return jsonify({'error': 'Miembro del proyecto no encontrado'}), 404
        
        # Verificar que el usuario actual es líder del proyecto
        current_member = ProjectMember.query.filter_by(
            project_id=member.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not current_member or current_member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para eliminar miembros de este proyecto'}), 403
        
        # No permitir eliminar al líder del proyecto
        if member.role == 'leader':
            return jsonify({'error': 'No se puede eliminar al líder del proyecto'}), 400
        
        # Desactivar en lugar de eliminar completamente
        member.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Miembro eliminado del proyecto exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400