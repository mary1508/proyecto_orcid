from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Milestone, Project, ProjectMember
from app.extensions import db
import uuid
from datetime import datetime

bp = Blueprint('milestones', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_milestone():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    required_fields = ['project_id', 'title', 'description', 'due_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        # Verificar que el usuario tiene permisos en el proyecto
        project_id = uuid.UUID(data['project_id'])
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role not in ['leader', 'manager']:
            return jsonify({'error': 'No tienes permisos para crear hitos en este proyecto'}), 403
        
        # Crear el hito
        milestone = Milestone.create(**data)
        
        return jsonify({
            'message': 'Hito creado exitosamente',
            'data': milestone.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_milestones():
    current_user_id = get_jwt_identity()
    project_id = request.args.get('project_id')
    
    if not project_id:
        return jsonify({'error': 'Se requiere el ID del proyecto'}), 400
    
    try:
        project_id = uuid.UUID(project_id)
        
        # Verificar que el usuario tenga acceso al proyecto
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member:
            return jsonify({'error': 'No tienes acceso a este proyecto'}), 403
        
        # Filtrar por estado
        status = request.args.get('status')
        query = Milestone.query.filter_by(project_id=project_id, is_active=True)
        
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar
        sort_by = request.args.get('sort_by', 'due_date')
        sort_dir = request.args.get('sort_dir', 'asc')
        
        if hasattr(Milestone, sort_by):
            order_column = getattr(Milestone, sort_by)
            if sort_dir.lower() == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # Paginar
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        paginated_query = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'data': [item.to_dict() for item in paginated_query.items],
            'total': paginated_query.total,
            'pages': paginated_query.pages,
            'current_page': page
        })
    except ValueError:
        return jsonify({'error': 'ID de proyecto inválido'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_milestone(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener el hito
        milestone = Milestone.query.filter_by(id=id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito no encontrado'}), 404
        
        # Verificar que el usuario tiene acceso al proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member:
            return jsonify({'error': 'No tienes acceso a este proyecto'}), 403
        
        return jsonify(milestone.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_milestone(id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener el hito
        milestone = Milestone.query.filter_by(id=id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito no encontrado'}), 404
        
        # Verificar que el usuario tiene permisos en el proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role not in ['leader', 'manager']:
            return jsonify({'error': 'No tienes permisos para actualizar hitos en este proyecto'}), 403
        
        # Actualizar campos
        for key, value in data.items():
            if hasattr(milestone, key) and key != 'id':
                setattr(milestone, key, value)
        
        milestone.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Hito actualizado exitosamente',
            'data': milestone.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_milestone(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener el hito
        milestone = Milestone.query.filter_by(id=id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito no encontrado'}), 404
        
        # Verificar que el usuario tiene permisos en el proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role not in ['leader', 'manager']:
            return jsonify({'error': 'No tienes permisos para eliminar hitos en este proyecto'}), 403
        
        # Marcar como inactivo en lugar de eliminar
        milestone.is_active = False
        milestone.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Hito eliminado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400