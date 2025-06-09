import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class BaseMixin:
    """Mixin que proporciona funcionalidad com�n para todos los modelos"""
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    @classmethod
    def get_by_id(cls, id):
        """Obtiene un registro por su ID"""
        instance = cls.query.filter_by(id=id, is_active=True).first_or_404()
        return instance

    @classmethod
    def create(cls, **kwargs):
        """Crea un nuevo registro"""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def update(cls, id, **kwargs):
        """Actualiza un registro existente"""
        instance = cls.get_by_id(id)
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.updated_at = datetime.utcnow()
        db.session.commit()
        return instance

    @classmethod
    def delete(cls, id):
        """Elimina un registro (soft delete)"""
        instance = cls.get_by_id(id)
        instance.is_active = False
        instance.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    def to_dict(self):
        """Convierte el modelo a un diccionario"""
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Manejar tipos especiales
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            data[column.name] = value
        return data


# 1. Modelo de pa�s
class Country(BaseMixin, db.Model):
    __tablename__ = 'countries'
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(2), nullable=False, unique=True)
    
    # Relaciones
    journals = db.relationship('Journal', backref='country', lazy=True)
    conferences = db.relationship('Conference', backref='country', lazy=True)


# 2. Modelo de usuario
class User(BaseMixin, db.Model):
    __tablename__ = 'users'
    
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', etc.
    orcid_id = db.Column(db.String(19), unique=True)
    
    # Relaciones
    refresh_tokens = db.relationship('RefreshToken', backref='user', lazy=True, cascade='all, delete-orphan')
    project_memberships = db.relationship('ProjectMember', backref='user', lazy=True)


# 3. Modelo de token de refresco
class RefreshToken(BaseMixin, db.Model):
    __tablename__ = 'refresh_tokens'
    
    token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)


# 4. Modelo de autor (puede ser diferente de usuario)
class Author(BaseMixin, db.Model):
    __tablename__ = 'authors'
    
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True)
    institution = db.Column(db.String(100))
    orcid_id = db.Column(db.String(19), unique=True)
    
    # Relaciones
    publication_authors = db.relationship('PublicationAuthor', backref='author', lazy=True, cascade='all, delete-orphan')


# 5. Modelo de tipo de publicaci�n
class PublicationType(BaseMixin, db.Model):
    __tablename__ = 'publication_types'
    
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relaciones
    publications = db.relationship('Publication', backref='publication_type', lazy=True)


# 6. Modelo de revista (journal)
class Journal(BaseMixin, db.Model):
    __tablename__ = 'journals'
    
    name = db.Column(db.String(100), nullable=False)
    issn = db.Column(db.String(9), unique=True)
    h_index = db.Column(db.Integer)
    quartile = db.Column(db.String(2)) # Q1, Q2, Q3, Q4
    description = db.Column(db.Text)
    publisher = db.Column(db.String(100))
    country_id = db.Column(UUID(as_uuid=True), db.ForeignKey('countries.id'))
    website = db.Column(db.String(255))
    
    # Relaciones
    publications = db.relationship('Publication', backref='journal', lazy=True)


# 7. Modelo de conferencia
class Conference(BaseMixin, db.Model):
    __tablename__ = 'conferences'
    
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100))
    h_index = db.Column(db.Integer)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    website = db.Column(db.String(255))
    country_id = db.Column(UUID(as_uuid=True), db.ForeignKey('countries.id'))
    
    # Relaciones
    publications = db.relationship('Publication', backref='conference', lazy=True)


# 8. Modelo de palabra clave
class Keyword(BaseMixin, db.Model):
    __tablename__ = 'keywords'
    
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    # Relaciones
    publication_keywords = db.relationship('PublicationKeyword', backref='keyword', lazy=True, cascade='all, delete-orphan')


from sqlalchemy.dialects.postgresql import UUID
import uuid

# 9. Modelo de publicación
class Publication(BaseMixin, db.Model):
    __tablename__ = 'publications'
    
    title = db.Column(db.String(255), nullable=False)
    abstract = db.Column(db.Text)
    doi = db.Column(db.String(100), unique=True)
    external_id = db.Column(db.Text, unique=True)  # Añadir este campo como texto
    publication_date = db.Column(db.Date)
    pdf_url = db.Column(db.String(255))
    url = db.Column(db.String(255))  # También agregar este campo que es usado en _create_publication_from_orcid
    year = db.Column(db.Integer)  # Agregar estos campos que son utilizados en el servicio
    month = db.Column(db.Integer)
    day = db.Column(db.Integer)
    publication_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('publication_types.id'), nullable=False)
    journal_id = db.Column(UUID(as_uuid=True), db.ForeignKey('journals.id'))
    conference_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conferences.id'))
    citation_count = db.Column(db.Integer, default=0)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'))
    
    
    # Relaciones
    authors = db.relationship('PublicationAuthor', backref='publication', lazy=True, cascade='all, delete-orphan')
    keywords = db.relationship('PublicationKeyword', backref='publication', lazy=True, cascade='all, delete-orphan')
    referenced_by = db.relationship(
        'PublicationReference',
        backref='referenced_publication',
        lazy=True,
        foreign_keys='PublicationReference.referenced_publication_id',
        cascade='all, delete-orphan'
    )
    references = db.relationship(
        'PublicationReference',
        backref='citing_publication',
        lazy=True,
        foreign_keys='PublicationReference.citing_publication_id',
        cascade='all, delete-orphan'
    )



# 10. Modelo de relaci�n publicaci�n-autor
class PublicationAuthor(BaseMixin, db.Model):
    __tablename__ = 'publication_authors'
    
    publication_id = db.Column(UUID(as_uuid=True), db.ForeignKey('publications.id'), nullable=False)
    author_id = db.Column(UUID(as_uuid=True), db.ForeignKey('authors.id'), nullable=False)
    is_corresponding = db.Column(db.Boolean, default=False)
    author_order = db.Column(db.Integer, nullable=False)


# 11. Modelo de relaci�n publicaci�n-keyword
class PublicationKeyword(BaseMixin, db.Model):
    __tablename__ = 'publication_keywords'
    
    publication_id = db.Column(UUID(as_uuid=True), db.ForeignKey('publications.id'), nullable=False)
    keyword_id = db.Column(UUID(as_uuid=True), db.ForeignKey('keywords.id'), nullable=False)


# 12. Modelo de referencia de publicaci�n
class PublicationReference(BaseMixin, db.Model):
    __tablename__ = 'publication_references'
    
    citing_publication_id = db.Column(UUID(as_uuid=True), db.ForeignKey('publications.id'), nullable=False)
    referenced_publication_id = db.Column(UUID(as_uuid=True), db.ForeignKey('publications.id'), nullable=False)
    reference_text = db.Column(db.Text)  # Para cuando la publicaci�n referenciada no est� en el sistema


# 13. Modelo de proyecto
class Project(BaseMixin, db.Model):
    __tablename__ = 'projects'
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(20), default='planificado')  # planificado, en_progreso, completado, etc.
    
    # Relaciones
    members = db.relationship('ProjectMember', backref='project', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')
    acquisitions = db.relationship('Acquisition', backref='project', lazy=True, cascade='all, delete-orphan')
    publications = db.relationship('Publication', backref='project', lazy=True)


# 14. Modelo de miembro de proyecto
class ProjectMember(BaseMixin, db.Model):
    __tablename__ = 'project_members'
    
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False) # investigador principal, co-investigador, asistente, etc.


# 15. Modelo de hito de proyecto
class Milestone(BaseMixin, db.Model):
    __tablename__ = 'milestones'
    
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendiente') # pendiente, en_progreso, completado, etc.
    
    # Relaciones
    deliverables = db.relationship('Deliverable', backref='milestone', lazy=True, cascade='all, delete-orphan')


# 16. Modelo de entregable
class Deliverable(BaseMixin, db.Model):
    __tablename__ = 'deliverables'
    
    milestone_id = db.Column(UUID(as_uuid=True), db.ForeignKey('milestones.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    file_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pendiente')  # pendiente, en_progreso, completado, etc.


# 17. Modelo de adquisici�n
class Acquisition(BaseMixin, db.Model):
    __tablename__ = 'acquisitions'
    
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    purchase_date = db.Column(db.Date)
    category = db.Column(db.String(50))  # equipo, materiales, servicios, etc.
    supplier = db.Column(db.String(100))
    invoice_number = db.Column(db.String(50))