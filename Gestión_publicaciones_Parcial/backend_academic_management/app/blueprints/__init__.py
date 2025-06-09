from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db

def register_blueprints(app):
    """Registra todos los blueprints en la aplicación Flask"""
    # Importaciones dinámicas para evitar circular imports
    from .countries import bp as countries_bp
    from .keywords import bp as keywords_bp
    from .publication_types import bp as publication_types_bp
    from .journals import bp as journals_bp
    from .conferences import bp as conferences_bp
    from .deliverables import bp as deliverables_bp
    from .milestones import bp as milestones_bp
    from .project_members import bp as project_members_bp
    from .refresh_tokens import bp as refresh_tokens_bp
    from .publication_references import bp as publication_references_bp
    from .publication_keywords import bp as publication_keywords_bp
    from .acquisitions import bp as acquisitions_bp
    from .users import bp as users_bp
    from .authors import bp as authors_bp
    from .publications import bp as publications_bp
    from .projects import bp as projects_bp
    from .publication_authors import bp as publication_authors_bp
    from .orcid import bp as orcid_bp
    from .auth import bp as auth_bp

    # Lista de todos los blueprints
    all_blueprints = [
        (countries_bp, '/api/countries'),
        (keywords_bp, '/api/keywords'),
        (publication_types_bp, '/api/publication-types'),
        (journals_bp, '/api/journals'),
        (conferences_bp, '/api/conferences'),
        (deliverables_bp, '/api/deliverables'),
        (milestones_bp, '/api/milestones'),
        (project_members_bp, '/api/project-members'),
        (refresh_tokens_bp, '/api/refresh-tokens'),
        (publication_references_bp, '/api/publication-references'),
        (publication_keywords_bp, '/api/publication-keywords'),
        (acquisitions_bp, '/api/acquisitions'),
        (users_bp, '/api/users'),
        (authors_bp, '/api/authors'),
        (publications_bp, '/api/publications'),
        (projects_bp, '/api/projects'),
        (publication_authors_bp, '/api/publication-authors'),
        (orcid_bp, '/api/orcid'),
        (auth_bp, '/api/auth')
    ]

    # Registrar cada blueprint
    for blueprint, url_prefix in all_blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)

    # Registrar ruta de health check
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'API funcionando correctamente'})