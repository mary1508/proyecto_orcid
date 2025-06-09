from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Author, PublicationAuthor, Publication
from app.extensions import db
import requests
import json

bp = Blueprint('authors', __name__)

@bp.route('/', methods=['POST'])
@jwt_required()
def create_author():
    data = request.get_json()
    
    # Verificar campos obligatorios
    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es obligatorio'}), 400
    
    try:
        author = Author.create(**data)
        return jsonify({
            'message': 'Autor creado exitosamente',
            'data': author.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['GET'])
@jwt_required()
def get_authors():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Filtro de búsqueda por nombre
    query = Author.query.filter_by(is_active=True)
    
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(
            (Author.first_name.ilike(search_term)) | 
            (Author.last_name.ilike(search_term))
        )
    
    # Ordenar
    sort_by = request.args.get('sort_by', 'last_name')
    sort_dir = request.args.get('sort_dir', 'asc')
    
    if hasattr(Author, sort_by):
        order_column = getattr(Author, sort_by)
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
def get_author(id):
    try:
        author = Author.get_by_id(id)
        author_data = author.to_dict()
        
        # Agregar publicaciones del autor
        publications = []
        author_publications = PublicationAuthor.query.filter_by(author_id=id).all()
        
        for pub_author in author_publications:
            publication = Publication.query.filter_by(id=pub_author.publication_id, is_active=True).first()
            if publication:
                publications.append({
                    'id': str(publication.id),
                    'title': publication.title,
                    'publication_date': publication.publication_date.isoformat() if publication.publication_date else None,
                    'doi': publication.doi,
                    'is_corresponding': pub_author.is_corresponding,
                    'author_order': pub_author.author_order
                })
        
        author_data['publications'] = publications
        
        return jsonify(author_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required()
def update_author(id):
    data = request.get_json()
    
    try:
        author = Author.update(id, **data)
        return jsonify({
            'message': 'Autor actualizado exitosamente',
            'data': author.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required()
def delete_author(id):
    try:
        Author.delete(id)
        return jsonify({
            'message': 'Autor eliminado exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/fetch-from-orcid', methods=['POST'])
@jwt_required()
def fetch_from_orcid():
    data = request.get_json()

    if not data or not data.get('orcid_id'):
        return jsonify({'error': 'Se requiere el ORCID ID'}), 400

    orcid_id = data['orcid_id']

    try:
        headers = {
            'Accept': 'application/json'
        }

        # Obtener datos del perfil
        response = requests.get(
            f'https://pub.orcid.org/v3.0/{orcid_id}/person',
            headers=headers
        )

        if response.status_code != 200:
            return jsonify({'error': f'Error al obtener datos de ORCID: {response.text}'}), 400

        profile_data = response.json() or {}

        # Obtener datos de las publicaciones
        works_response = requests.get(
            f'https://pub.orcid.org/v3.0/{orcid_id}/works',
            headers=headers
        )

        if works_response.status_code != 200:
            return jsonify({'error': f'Error al obtener publicaciones de ORCID: {works_response.text}'}), 400

        works_data = works_response.json() or {}

        # Extraer nombre
        name_data = profile_data.get('name') or {}
        given_names = name_data.get('given-names') or {}
        family_name = name_data.get('family-name') or {}

        first_name = given_names.get('value', '')
        last_name = family_name.get('value', '')

        # Extraer email
        emails_data = profile_data.get('emails') or {}
        email_list = emails_data.get('email') or []
        email = None
        if isinstance(email_list, list) and len(email_list) > 0:
            email = email_list[0].get('email')

        # Verificar si el autor ya existe
        existing_author = Author.query.filter_by(orcid_id=orcid_id).first()

        if existing_author:
            author = Author.update(
                existing_author.id,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
        else:
            author = Author.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                orcid_id=orcid_id
            )

        # Procesar publicaciones
        publications_summary = []

        for group in works_data.get('group', []):
            work_summaries = group.get('work-summary') or []
            if not work_summaries:
                continue

            summary = work_summaries[0] or {}

            title_data = summary.get('title') or {}
            inner_title = title_data.get('title') or {}
            title = inner_title.get('value', 'Sin título')

            pub_data = {
                'title': title,
                'type': summary.get('type', ''),
                'publication_date': None,
                'journal': None,
                'doi': None
            }

            # Fecha
            pub_date = summary.get('publication-date') or {}
            year = (pub_date.get('year') or {}).get('value')
            month = (pub_date.get('month') or {}).get('value', '01')
            day = (pub_date.get('day') or {}).get('value', '01')

            if year:
                pub_data['publication_date'] = f"{year}-{month}-{day}"

            # DOI
            external_ids = summary.get('external-ids') or {}
            ext_id_list = external_ids.get('external-id') or []
            for ext_id in ext_id_list:
                if ext_id.get('external-id-type') == 'doi':
                    pub_data['doi'] = ext_id.get('external-id-value')

            # Journal
            journal_data = summary.get('journal-title') or {}
            pub_data['journal'] = journal_data.get('value')

            publications_summary.append(pub_data)

        return jsonify({
            'message': 'Datos obtenidos exitosamente de ORCID',
            'author': author.to_dict(),
            'publications': publications_summary
        })

    except Exception as e:
        import traceback
        traceback.print_exc()  # Para depuración en consola
        return jsonify({'error': f'Error al procesar datos de ORCID: {str(e)}'}), 500
