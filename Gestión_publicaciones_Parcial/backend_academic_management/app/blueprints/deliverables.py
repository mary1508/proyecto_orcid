from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Deliverable, Milestone, ProjectMember
from app.extensions import db
import uuid
from datetime import datetime

bp = Blueprint('deliverables', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_deliverable():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    required_fields = ['milestone_id', 'title', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        # Obtener el hito para verificar el proyecto
        milestone_id = uuid.UUID(data['milestone_id'])
        milestone = Milestone.query.filter_by(id=milestone_id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito no encontrado'}), 404
        
        # Verificar que el usuario tiene permisos en el proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role not in ['leader', 'manager']:
            return jsonify({'error': 'No tienes permisos para crear entregables en este proyecto'}), 403
        
        # Crear el entregable
        deliverable = Deliverable.create(**data)
        
        return jsonify({
            'message': 'Entregable creado exitosamente',
            'data': deliverable.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_deliverables():
    current_user_id = get_jwt_identity()
    milestone_id = request.args.get('milestone_id')
    
    if not milestone_id:
        return jsonify({'error': 'Se requiere el ID del hito'}), 400
    
    try:
        milestone_id = uuid.UUID(milestone_id)
        
        # Obtener el hito para verificar el proyecto
        milestone = Milestone.query.filter_by(id=milestone_id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito no encontrado'}), 404
        
        # Verificar que el usuario tenga acceso al proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member:
            return jsonify({'error': 'No tienes acceso a este proyecto'}), 403
        
        # Filtrar por estado
        status = request.args.get('status')
        query = Deliverable.query.filter_by(milestone_id=milestone_id, is_active=True)
        
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar
        sort_by = request.args.get('sort_by', 'created_at')
        sort_dir = request.args.get('sort_dir', 'desc')
        
        if hasattr(Deliverable, sort_by):
            order_column = getattr(Deliverable, sort_by)
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
        return jsonify({'error': 'ID de hito inválido'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_deliverable(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener el entregable
        deliverable = Deliverable.query.filter_by(id=id, is_active=True).first()
        
        if not deliverable:
            return jsonify({'error': 'Entregable no encontrado'}), 404
        
        # Obtener el hito asociado
        milestone = Milestone.query.filter_by(id=deliverable.milestone_id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito asociado no encontrado'}), 404
        
        # Verificar que el usuario tiene acceso al proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member:
            return jsonify({'error': 'No tienes acceso a este proyecto'}), 403
        
        return jsonify(deliverable.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_deliverable(id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener el entregable
        deliverable = Deliverable.query.filter_by(id=id, is_active=True).first()
        
        if not deliverable:
            return jsonify({'error': 'Entregable no encontrado'}), 404
        
        # Obtener el hito asociado
        milestone = Milestone.query.filter_by(id=deliverable.milestone_id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito asociado no encontrado'}), 404
        
        # Verificar que el usuario tiene permisos en el proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role not in ['leader', 'manager']:
            return jsonify({'error': 'No tienes permisos para actualizar entregables en este proyecto'}), 403
        
        # Actualizar campos
        for key, value in data.items():
            if hasattr(deliverable, key) and key not in ['id', 'milestone_id']:
                setattr(deliverable, key, value)
        
        deliverable.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Entregable actualizado exitosamente',
            'data': deliverable.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_deliverable(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Obtener el entregable
        deliverable = Deliverable.query.filter_by(id=id, is_active=True).first()
        
        if not deliverable:
            return jsonify({'error': 'Entregable no encontrado'}), 404
        
        # Obtener el hito asociado
        milestone = Milestone.query.filter_by(id=deliverable.milestone_id, is_active=True).first()
        
        if not milestone:
            return jsonify({'error': 'Hito asociado no encontrado'}), 404
        
        # Verificar que el usuario tiene permisos en el proyecto
        member = ProjectMember.query.filter_by(
            project_id=milestone.project_id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role not in ['leader', 'manager']:
            return jsonify({'error': 'No tienes permisos para eliminar entregables en este proyecto'}), 403
        
        # Marcar como inactivo en lugar de eliminar
        deliverable.is_active = False
        deliverable.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Entregable eliminado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400