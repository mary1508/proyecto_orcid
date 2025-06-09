from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Publication, PublicationAuthor, PublicationKeyword, Author, Keyword
from app.extensions import db
import uuid

bp = Blueprint('publications', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_publication():
    data = request.get_json()
    
    # Verificar campos obligatorios
    required_fields = ['title', 'publication_type_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        # Crear la publicación, incluyendo el campo external_id si se proporciona
        publication = Publication.create(**{
            k: v for k, v in data.items() 
            if k not in ['authors', 'keywords']
        })
        
        # Procesar autores si se proporcionan
        if 'authors' in data and isinstance(data['authors'], list):
            for idx, author_data in enumerate(data['authors']):
                if isinstance(author_data, dict) and 'author_id' in author_data:
                    PublicationAuthor.create(
                        publication_id=publication.id,
                        author_id=uuid.UUID(author_data['author_id']),
                        is_corresponding=author_data.get('is_corresponding', False),
                        author_order=author_data.get('author_order', idx + 1)
                    )
        
        # Procesar keywords si se proporcionan
        if 'keywords' in data and isinstance(data['keywords'], list):
            for keyword_id in data['keywords']:
                PublicationKeyword.create(
                    publication_id=publication.id,
                    keyword_id=uuid.UUID(keyword_id)
                )
        
        return jsonify({
            'message': 'Publicación creada exitosamente',
            'data': publication.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_publications():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Filtros opcionales
    filters = {}
    
    # Filtrar por tipo de publicación
    if request.args.get('publication_type_id'):
        filters['publication_type_id'] = uuid.UUID(request.args.get('publication_type_id'))
    
    # Filtrar por journal
    if request.args.get('journal_id'):
        filters['journal_id'] = uuid.UUID(request.args.get('journal_id'))
    
    # Filtrar por conferencia
    if request.args.get('conference_id'):
        filters['conference_id'] = uuid.UUID(request.args.get('conference_id'))
    
    # Filtrar por proyecto
    if request.args.get('project_id'):
        filters['project_id'] = uuid.UUID(request.args.get('project_id'))
    
    # Aplicar filtros
    query = Publication.query.filter_by(is_active=True, **filters)
    
    # Buscar por título
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(Publication.title.ilike(search_term))
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')
    
    if hasattr(Publication, sort_by):
        order_column = getattr(Publication, sort_by)
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
    
    # Agregar datos básicos de publicaciones
    for item in paginated_query.items:
        publication_data = item.to_dict()
        
        # Agregar autores
        authors = []
        for pub_author in PublicationAuthor.query.filter_by(publication_id=item.id).all():
            author = Author.query.get(pub_author.author_id)
            if author:
                authors.append({
                    'id': str(author.id),
                    'first_name': author.first_name,
                    'last_name': author.last_name,
                    'is_corresponding': pub_author.is_corresponding,
                    'author_order': pub_author.author_order
                })
        publication_data['authors'] = authors
        
        # Agregar keywords
        keywords = []
        for pub_keyword in PublicationKeyword.query.filter_by(publication_id=item.id).all():
            keyword = Keyword.query.get(pub_keyword.keyword_id)
            if keyword:
                keywords.append({
                    'id': str(keyword.id),
                    'name': keyword.name
                })
        publication_data['keywords'] = keywords
        
        result['data'].append(publication_data)
    
    return jsonify(result)

@bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_publication(id):
    try:
        publication = Publication.get_by_id(id)
        publication_data = publication.to_dict()
        
        # Añadir autores
        authors = []
        for pub_author in PublicationAuthor.query.filter_by(publication_id=id).all():
            author = Author.query.get(pub_author.author_id)
            if author:
                authors.append({
                    'id': str(author.id),
                    'first_name': author.first_name,
                    'last_name': author.last_name,
                    'email': author.email,
                    'institution': author.institution,
                    'orcid_id': author.orcid_id,
                    'is_corresponding': pub_author.is_corresponding,
                    'author_order': pub_author.author_order
                })
        publication_data['authors'] = authors
        
        # Añadir keywords
        keywords = []
        for pub_keyword in PublicationKeyword.query.filter_by(publication_id=id).all():
            keyword = Keyword.query.get(pub_keyword.keyword_id)
            if keyword:
                keywords.append({
                    'id': str(keyword.id),
                    'name': keyword.name
                })
        publication_data['keywords'] = keywords
        
        return jsonify(publication_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_publication(id):
    data = request.get_json()
    
    try:
        # Actualizar campos de publicación
        publication_fields = {
            k: v for k, v in data.items() 
            if k not in ['authors', 'keywords']
        }
        
        publication = Publication.update(id, **publication_fields)
        
        # Actualizar autores si se proporcionan
        if 'authors' in data and isinstance(data['authors'], list):
            # Eliminar autores existentes
            PublicationAuthor.query.filter_by(publication_id=id).delete()
            
            # Agregar nuevos autores
            for idx, author_data in enumerate(data['authors']):
                if isinstance(author_data, dict) and 'author_id' in author_data:
                    PublicationAuthor.create(
                        publication_id=publication.id,
                        author_id=uuid.UUID(author_data['author_id']),
                        is_corresponding=author_data.get('is_corresponding', False),
                        author_order=author_data.get('author_order', idx + 1)
                    )
        
        # Actualizar keywords si se proporcionan
        if 'keywords' in data and isinstance(data['keywords'], list):
            # Eliminar keywords existentes
            PublicationKeyword.query.filter_by(publication_id=id).delete()
            
            # Agregar nuevas keywords
            for keyword_id in data['keywords']:
                PublicationKeyword.create(
                    publication_id=publication.id,
                    keyword_id=uuid.UUID(keyword_id)
                )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Publicación actualizada exitosamente',
            'data': publication.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_publication(id):
    try:
        Publication.delete(id)
        return jsonify({
            'message': 'Publicación eliminada exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
