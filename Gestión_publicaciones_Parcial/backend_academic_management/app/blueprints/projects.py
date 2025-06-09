from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Project, ProjectMember, User
from app.extensions import db
import uuid

bp = Blueprint('projects', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_project():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Verificar campos obligatorios
    required_fields = ['title', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        # Crear proyecto
        project = Project.create(**{
            k: v for k, v in data.items() 
            if k not in ['members']
        })
        
        # Agregar al usuario actual como miembro del proyecto (líder)
        ProjectMember.create(
            project_id=project.id,
            user_id=uuid.UUID(current_user_id),
            role='leader',
            is_active=True
        )
        
        # Agregar miembros adicionales si se proporcionan
        if 'members' in data and isinstance(data['members'], list):
            for member_data in data['members']:
                if isinstance(member_data, dict) and 'user_id' in member_data:
                    ProjectMember.create(
                        project_id=project.id,
                        user_id=uuid.UUID(member_data['user_id']),
                        role=member_data.get('role', 'member'),
                        is_active=True
                    )
        
        return jsonify({
            'message': 'Proyecto creado exitosamente',
            'data': project.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_projects():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    current_user_id = get_jwt_identity()
    
    # Opciones de filtrado
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    show_mine = request.args.get('show_mine', 'false').lower() == 'true'
    
    # Base query
    query = Project.query.filter_by(is_active=True)
    
    # Filtrar solo proyectos del usuario actual si se solicita
    if show_mine:
        query = query.join(ProjectMember).filter(
            ProjectMember.user_id == uuid.UUID(current_user_id),
            ProjectMember.is_active == True
        )
    
    # Filtro de búsqueda por título
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(Project.title.ilike(search_term))
    
    # Filtro por estado
    if request.args.get('status'):
        query = query.filter(Project.status == request.args.get('status'))
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')
    
    if hasattr(Project, sort_by):
        order_column = getattr(Project, sort_by)
        if sort_dir.lower() == 'desc':
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # Paginar
    paginated_query = query.paginate(page=page, per_page=per_page)
    
    # Preparar respuesta
    result = {
        'data': [],
        'total': paginated_query.total,
        'pages': paginated_query.pages,
        'current_page': page
    }
    
    # Agregar datos básicos de proyectos
    for item in paginated_query.items:
        project_data = item.to_dict()
        
        # Agregar miembros (sólo información básica)
        members = []
        for project_member in ProjectMember.query.filter_by(project_id=item.id, is_active=True).all():
            user = User.query.get(project_member.user_id)
            if user:
                members.append({
                    'id': str(user.id),
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': project_member.role
                })
        project_data['members'] = members
        
        result['data'].append(project_data)
    
    return jsonify(result)

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_project(id):
    try:
        project = Project.get_by_id(id)
        project_data = project.to_dict()
        
        # Añadir miembros del proyecto
        members = []
        for project_member in ProjectMember.query.filter_by(project_id=id, is_active=True).all():
            user = User.query.get(project_member.user_id)
            if user:
                members.append({
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': project_member.role,
                    'created_at': project_member.created_at.isoformat() if project_member.created_at else None
                })
        project_data['members'] = members
        
        return jsonify(project_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_project(id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que el usuario actual sea miembro del proyecto con rol leader
        member = ProjectMember.query.filter_by(
            project_id=id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para actualizar este proyecto'}), 403
        
        # Actualizar campos de proyecto
        project_fields = {
            k: v for k, v in data.items() 
            if k not in ['members']
        }
        
        project = Project.update(id, **project_fields)
        
        # Actualizar miembros si se proporcionan
        if 'members' in data and isinstance(data['members'], list):
            for member_data in data['members']:
                if isinstance(member_data, dict) and 'user_id' in member_data:
                    user_id = uuid.UUID(member_data['user_id'])
                    existing_member = ProjectMember.query.filter_by(
                        project_id=id,
                        user_id=user_id
                    ).first()
                    
                    if existing_member:
                        # Actualizar miembro existente
                        existing_member.role = member_data.get('role', existing_member.role)
                        existing_member.is_active = member_data.get('is_active', existing_member.is_active)
                    else:
                        # Crear nuevo miembro
                        ProjectMember.create(
                            project_id=id,
                            user_id=user_id,
                            role=member_data.get('role', 'member'),
                            is_active=True
                        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Proyecto actualizado exitosamente',
            'data': project.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_project(id):
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que el usuario actual sea miembro del proyecto con rol leader
        member = ProjectMember.query.filter_by(
            project_id=id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not member or member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para eliminar este proyecto'}), 403
        
        Project.delete(id)
        return jsonify({
            'message': 'Proyecto eliminado exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>/members', methods=['GET'])
@jwt_required()
def get_project_members(id):
    try:
        Project.get_by_id(id)  # Verificar que el proyecto existe
        
        members = []
        for project_member in ProjectMember.query.filter_by(project_id=id, is_active=True).all():
            user = User.query.get(project_member.user_id)
            if user:
                members.append({
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': project_member.role,
                    'created_at': project_member.created_at.isoformat() if project_member.created_at else None
                })
        
        return jsonify({
            'data': members,
            'total': len(members)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>/members/<uuid:user_id>', methods=['PUT'])
@jwt_required()
def update_project_member(id, user_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que el usuario actual sea miembro del proyecto con rol leader
        current_member = ProjectMember.query.filter_by(
            project_id=id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not current_member or current_member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para modificar miembros de este proyecto'}), 403
        
        # Buscar miembro a actualizar
        member = ProjectMember.query.filter_by(
            project_id=id,
            user_id=user_id
        ).first()
        
        if not member:
            # Crear nuevo miembro
            member = ProjectMember(
                project_id=id,
                user_id=user_id,
                role=data.get('role', 'member'),
                is_active=True
            )
            db.session.add(member)
        else:
            # Actualizar miembro existente
            if 'role' in data:
                member.role = data['role']
            if 'is_active' in data:
                member.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Miembro del proyecto actualizado exitosamente',
            'data': {
                'user_id': str(member.user_id),
                'project_id': str(member.project_id),
                'role': member.role,
                'is_active': member.is_active
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>/members/<uuid:user_id>', methods=['DELETE'])
@jwt_required()
def remove_project_member(id, user_id):
    current_user_id = get_jwt_identity()
    
    try:
        # Verificar que el usuario actual sea miembro del proyecto con rol leader
        current_member = ProjectMember.query.filter_by(
            project_id=id,
            user_id=uuid.UUID(current_user_id),
            is_active=True
        ).first()
        
        if not current_member or current_member.role != 'leader':
            return jsonify({'error': 'No tienes permisos para eliminar miembros de este proyecto'}), 403
        
        # No permitir eliminar al líder del proyecto
        member_to_remove = ProjectMember.query.filter_by(
            project_id=id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not member_to_remove:
            return jsonify({'error': 'El miembro no existe en el proyecto'}), 404
        
        if member_to_remove.role == 'leader':
            return jsonify({'error': 'No se puede eliminar al líder del proyecto'}), 400
        
        # Desactivar en lugar de eliminar completamente
        member_to_remove.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Miembro eliminado del proyecto exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400