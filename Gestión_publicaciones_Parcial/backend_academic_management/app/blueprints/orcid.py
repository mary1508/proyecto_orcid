from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.services.orcid_service import OrcidService

bp = Blueprint('orcid', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_orcid_info():
    """Punto final para verificar el servicio de ORCID"""
    return jsonify({
        'status': 'active',
        'message': 'Servicio de integración con ORCID disponible'
    })

@bp.route('/sync/<orcid_id>', methods=['POST'])
@jwt_required()
def sync_researcher(orcid_id):
    """Sincroniza datos de un investigador desde ORCID"""
    result = OrcidService.sync_researcher_data(orcid_id)
    return jsonify(result)

@bp.route('/researcher/<orcid_id>', methods=['GET'])
@jwt_required()
def get_researcher(orcid_id):
    """Obtiene información básica de un investigador por su ORCID ID"""
    researcher_info = OrcidService.get_researcher_info(orcid_id)
    
    if not researcher_info:
        return jsonify({
            'success': False,
            'message': 'No se pudo obtener información del investigador'
        }), 404
    
    person = researcher_info.get('person', {})
    name = person.get('name', {})
    
    researcher_data = {
        'orcid_id': orcid_id,
        'first_name': name.get('given-names', {}).get('value', ''),
        'last_name': name.get('family-name', {}).get('value', ''),
        'credit_name': name.get('credit-name', {}).get('value', ''),
        'email': OrcidService._extract_email(person),
        'affiliation': OrcidService._extract_affiliation(person)
    }
    
    return jsonify({
        'success': True,
        'data': researcher_data
    })

@bp.route('/researcher/<orcid_id>/works', methods=['GET'])
@jwt_required()
def get_works(orcid_id):
    """Obtiene las publicaciones de un investigador por su ORCID ID"""
    works = OrcidService.get_researcher_works(orcid_id)
    
    if not works:
        return jsonify({
            'success': False,
            'message': 'No se pudieron obtener las publicaciones del investigador'
        }), 404
    
    simplified_works = []

    for work_group in works:
        work = OrcidService._get_preferred_work(work_group)
        if work:
            external_id = OrcidService._extract_external_id(work)

            # Asegurarse de que journal-title no sea None
            journal_info = work.get('journal-title')
            journal = journal_info.get('value', '') if journal_info else ''

            simplified_works.append({
                'title': work.get('title', {}).get('title', {}).get('value', 'Sin título'),
                'type': work.get('type'),
                'year': OrcidService._extract_year(work),
                'journal': journal,
                'external_id': external_id,
                'doi': OrcidService._extract_doi(work),
                'url': OrcidService._extract_url(work)
            })
    
    return jsonify({
        'success': True,
        'count': len(simplified_works),
        'data': simplified_works
    })
