import requests
import os
import uuid
import logging
from datetime import date
from dotenv import load_dotenv
from app.extensions import db
from app.models import Author, Publication, PublicationAuthor, Journal, Conference, PublicationType

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('orcid_service')

load_dotenv()

class OrcidService:
    """Servicio para interactuar con la API de ORCID"""
    
    BASE_URL = "https://pub.orcid.org/v3.0"
    HEADERS = {"Accept": "application/json"}
    
    @classmethod
    def get_researcher_info(cls, orcid_id):
        """Obtiene información básica de un investigador por su ORCID ID"""
        url = f"{cls.BASE_URL}/{orcid_id}"
        try:
            response = requests.get(url, headers=cls.HEADERS, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get researcher info: {response.status_code}")
                return None
                
            return response.json()
        except Exception as e:
            logger.error(f"Error getting researcher info: {str(e)}")
            return None
        
    @classmethod
    def get_researcher_works(cls, orcid_id):
        """Obtiene las publicaciones de un investigador por su ORCID ID"""
        url = f"{cls.BASE_URL}/{orcid_id}/works"
        try:
            response = requests.get(url, headers=cls.HEADERS, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get works: {response.status_code}")
                return []
                
            return response.json().get('group', [])
        except Exception as e:
            logger.error(f"Error getting researcher works: {str(e)}")
            return []
    
    @classmethod
    def sync_researcher_data(cls, orcid_id):
        """Sincroniza datos de un investigador desde ORCID a la base de datos local"""
        # Obtenemos info básica del investigador
        researcher_info = cls.get_researcher_info(orcid_id)
        if not researcher_info:
            return {"success": False, "message": "No se pudo obtener información del investigador"}
        
        # Extraemos los datos personales
        person = researcher_info.get('person', {})
        name = person.get('name', {})
        first_name = name.get('given-names', {}).get('value', '')
        last_name = name.get('family-name', {}).get('value', '')
        
        # Verificamos si el autor ya existe en nuestra base de datos
        author = Author.query.filter_by(orcid_id=orcid_id).first()
        
        if not author:
            # Creamos un nuevo autor
            try:
                author = Author(
                    first_name=first_name,
                    last_name=last_name,
                    orcid_id=orcid_id,
                    email=cls._extract_email(person),
                    institution=cls._extract_affiliation(person)
                )
                db.session.add(author)
                db.session.commit()
                logger.info(f"Created new author: {first_name} {last_name} with ORCID: {orcid_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to create author: {str(e)}")
                return {"success": False, "message": f"Error al crear autor: {str(e)}"}
        
        # Obtenemos las publicaciones del investigador
        works = cls.get_researcher_works(orcid_id)
        publications_added = 0
        publications_skipped = 0
        publications_failed = 0
        
        logger.info(f"Found {len(works)} work groups for ORCID ID: {orcid_id}")
        
        # Primero, verificar que los tipos de publicación existan
        article_type = PublicationType.query.filter_by(name='Artículo').first()
        conference_type = PublicationType.query.filter_by(name='Conferencia').first()
        
        # Si no existen, crearlos (esto evita errores por IDs fijos)
        if not article_type:
            article_type = PublicationType(name='Artículo', description='Artículo en revista científica')
            db.session.add(article_type)
            
        if not conference_type:
            conference_type = PublicationType(name='Conferencia', description='Publicación en conferencia')
            db.session.add(conference_type)
            
        db.session.commit()
        
        for work_group in works:
            try:
                # Cada grupo puede tener varias versiones de la misma publicación
                work = cls._get_preferred_work(work_group)
                if not work:
                    logger.info("Skipping work group - no preferred work found")
                    publications_skipped += 1
                    continue
                    
                # Verificamos si la publicación ya existe por identificador externo
                pub_external_id = cls._extract_external_id(work)
                if not pub_external_id:
                    logger.info("Skipping work - no external ID found")
                    publications_skipped += 1
                    continue
                
                logger.info(f"Processing work with external ID: {pub_external_id}")
                
                # Verificar si la publicación existe por DOI primero (más confiable)
                doi = cls._extract_doi(work)
                existing_pub = None
                
                if doi:
                    existing_pub = Publication.query.filter_by(doi=doi).first()
                    
                # Si no se encontró por DOI, buscar por external_id
                if not existing_pub and pub_external_id:
                    try:
                        existing_pub = Publication.query.filter_by(external_id=pub_external_id).first()
                    except Exception as e:
                        logger.error(f"Error al buscar publicación por external_id: {str(e)}")
                        # Si hay un error (como la columna no existe), simplemente continuamos
                        existing_pub = None
                
                if existing_pub:
                    # Si ya existe, solo nos aseguramos que el autor esté vinculado
                    logger.info(f"Publication already exists with ID: {existing_pub.id}")
                    cls._ensure_author_linked(existing_pub.id, author.id)
                    publications_skipped += 1
                    continue
                
                # Creamos la publicación
                publication = cls._create_publication_from_orcid(work, pub_external_id, article_type.id, conference_type.id)
                if publication:
                    # Vinculamos el autor con la publicación
                    cls._ensure_author_linked(publication.id, author.id)
                    publications_added += 1
                    logger.info(f"Added new publication: {publication.title}")
                    
                    # Commit después de cada publicación exitosa para evitar perder todo por un error
                    db.session.commit()
                else:
                    publications_failed += 1
                    logger.error(f"Failed to create publication for work: {work.get('title', {}).get('title', {}).get('value', 'Unknown')}")
                    
            except Exception as e:
                db.session.rollback()
                publications_failed += 1
                logger.error(f"Error processing work: {str(e)}")
        
        return {
            "success": True,
            "message": f"Datos sincronizados correctamente. {publications_added} publicaciones agregadas, {publications_skipped} ya existentes, {publications_failed} fallidas.",
            "author": {
                "id": str(author.id),
                "name": f"{author.first_name} {author.last_name}",
                "orcid_id": author.orcid_id
            },
            "stats": {
                "added": publications_added,
                "skipped": publications_skipped,
                "failed": publications_failed
            }
        }
    
    @staticmethod
    def _extract_email(person):
        """Extrae el email de los datos de persona de ORCID"""
        if not person:
            return ''
            
        emails = person.get('emails', {}) or {}
        email_list = emails.get('email', []) or []
        
        if email_list and len(email_list) > 0:
            email_obj = email_list[0] or {}
            return email_obj.get('email', '')
        return ''
    
    @staticmethod
    def _extract_affiliation(person):
        """Extrae la afiliación de los datos de persona de ORCID"""
        if not person:
            return ''
            
        employments = person.get('employments', {}) or {}
        affiliations = employments.get('employment-summary', []) or []
        
        if affiliations and len(affiliations) > 0:
            org = affiliations[0].get('organization', {}) or {}
            return org.get('name', '')
        return ''
    
    @staticmethod
    def _get_preferred_work(work_group):
        """Obtiene la versión preferida de una publicación del grupo de trabajos"""
        if not work_group:
            return None
            
        works = work_group.get('work-summary', []) or []
        if not works:
            return None
            
        # Preferimos la versión con más detalles
        return max(works, key=lambda w: len(str(w)))
    
    @staticmethod
    def _extract_external_id(work):
        """Extrae un identificador externo único para la publicación"""
        if not work:
            return None
            
        external_ids_obj = work.get('external-ids', {}) or {}
        external_ids = external_ids_obj.get('external-id', []) or []
        
        # Preferimos el DOI como identificador
        for ext_id in external_ids:
            if ext_id.get('external-id-type') == 'doi':
                return f"doi:{ext_id.get('external-id-value', '')}"
        
        # Si no hay DOI, usamos cualquier otro identificador disponible
        if external_ids and len(external_ids) > 0:
            id_type = external_ids[0].get('external-id-type', '')
            id_value = external_ids[0].get('external-id-value', '')
            if id_type and id_value:
                return f"{id_type}:{id_value}"
        
        # Si no hay identificadores, usamos el put-code de ORCID
        put_code = work.get('put-code', '')
        if put_code:
            return f"orcid_work:{put_code}"
        
        # Último recurso: usar el título como identificador
        title_obj = work.get('title', {}) or {}
        title_data = title_obj.get('title', {}) or {}
        title = title_data.get('value', '')
        
        if title:
            return f"title:{title}"
        
        return None
    
    @classmethod
    def _create_publication_from_orcid(cls, work, external_id, article_type_id, conference_type_id):
        """Crea una publicación en nuestra base de datos a partir de los datos de ORCID"""
        try:
            if not work:
                logger.error("Work data is None or empty")
                return None
                
            # Extraemos los datos básicos de la publicación
            title_obj = work.get('title', {}) or {}
            title_data = title_obj.get('title', {}) or {}
            title = title_data.get('value') or 'Sin título'
            
            # Determinamos si es una conferencia o un journal
            publication_type_id = article_type_id  # Por defecto, asumimos que es un artículo
            journal_id = None
            conference_id = None
            
            # Extraemos datos de la fuente (journal o conferencia)
            journal_title_obj = work.get('journal-title') or {}
            source = journal_title_obj.get('value', '')
            
            if source:
                # Es un journal
                try:
                    # Buscamos si ya existe el journal, si no, lo creamos
                    journal = Journal.query.filter_by(name=source).first()
                    if not journal:
                        country = cls._get_default_country()
                        journal = Journal(
                            name=source,
                            country_id=country.id if country else None,
                            quartile="Q4",    # Quartil por defecto
                            h_index=0      # H-index por defecto
                        )
                        db.session.add(journal)
                        db.session.flush()
                    
                    journal_id = journal.id if journal else None
                except Exception as e:
                    logger.error(f"Error creating/finding journal: {str(e)}")
                    journal_id = None
            else:
                # Si no hay journal, asumimos que es una conferencia
                publication_type_id = conference_type_id
                
                try:
                    # Creamos una conferencia con datos mínimos
                    country = cls._get_default_country()
                    pub_year = cls._extract_year(work) or 2023
                    
                    conference_name = f"Conferencia - {title[:50]}"
                    conference = Conference.query.filter_by(name=conference_name, year=pub_year).first()
                    
                    if not conference:
                        conference = Conference(
                            name=conference_name,
                            year=pub_year,
                            country_id=country.id if country else None,
                            description="Importado desde ORCID"
                        )
                        db.session.add(conference)
                        db.session.flush()
                    
                    conference_id = conference.id if conference else None
                except Exception as e:
                    logger.error(f"Error creating/finding conference: {str(e)}")
                    conference_id = None
            
            # Extraer fecha de publicación
            year = cls._extract_year(work)
            month = cls._extract_month(work)
            day = cls._extract_day(work)
            
            # Construir la fecha de publicación si hay suficientes datos
            publication_date = None
            if year:
                try:
                    publication_date = date(year, month or 1, day or 1)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid date values: year={year}, month={month}, day={day}. Error: {str(e)}")
                    publication_date = None
            
            # Extracción segura de abstract
            abstract = ''
            if 'short-description' in work and work['short-description'] is not None:
                abstract = work['short-description']
            
            # Creamos la publicación con los datos obligatorios
            publication_data = {
                'title': title,
                'abstract': abstract,
                'publication_type_id': publication_type_id,
            }
            
            # Agregar campos opcionales si tienen valor
            optional_fields = {
                'doi': cls._extract_doi(work),
                'publication_date': publication_date,
                'external_id': external_id,
                'url': cls._extract_url(work),
                'year': year,
                'month': month if month is not None else None,
                'day': day if day is not None else None,
                'journal_id': journal_id,
                'conference_id': conference_id
            }
            
            # Solo agregamos los campos que tienen valor y están en el modelo
            for field, value in optional_fields.items():
                if value is not None and hasattr(Publication, field):
                    publication_data[field] = value
            
            # Creamos la publicación
            publication = Publication(**publication_data)
            db.session.add(publication)
            db.session.flush()
            
            return publication
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error detallado al crear publicación: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _ensure_author_linked(publication_id, author_id):
        """Asegura que el autor esté vinculado a la publicación"""
        if not publication_id or not author_id:
            logger.warning("Cannot link author: missing publication_id or author_id")
            return False
            
        try:
            # Verificamos si el vínculo ya existe
            pub_author = PublicationAuthor.query.filter_by(
                publication_id=publication_id,
                author_id=author_id
            ).first()
            
            if not pub_author:
                # Determinar el siguiente orden de autor
                max_order = db.session.query(db.func.max(PublicationAuthor.author_order)).filter_by(
                    publication_id=publication_id
                ).scalar()
                
                next_order = 1 if max_order is None else max_order + 1
                
                # Creamos el vínculo
                pub_author = PublicationAuthor(
                    publication_id=publication_id,
                    author_id=author_id,
                    is_corresponding=False,  # Por defecto, no es autor correspondiente
                    author_order=next_order  # Asignamos el siguiente orden
                )
                db.session.add(pub_author)
                db.session.flush()
            
            return True
        except Exception as e:
            logger.error(f"Error linking author to publication: {str(e)}")
            return False
    
    @staticmethod
    def _extract_year(work):
        """Extrae el año de publicación"""
        if not work or 'publication-date' not in work:
            return None
            
        publication_date = work.get('publication-date') or {}
        year_obj = publication_date.get('year') or {}
        year_value = year_obj.get('value')
        
        if year_value and year_value.isdigit():
            return int(year_value)
        return None
    
    @staticmethod
    def _extract_month(work):
        """Extrae el mes de publicación"""
        if not work or 'publication-date' not in work:
            return None
            
        publication_date = work.get('publication-date') or {}
        month_obj = publication_date.get('month') or {}
        month_value = month_obj.get('value')
        
        if month_value and month_value.isdigit():
            month_int = int(month_value)
            if 1 <= month_int <= 12:  # Validamos que sea un mes válido
                return month_int
        return None
    
    @staticmethod
    def _extract_day(work):
        """Extrae el día de publicación"""
        if not work or 'publication-date' not in work:
            return None
            
        publication_date = work.get('publication-date') or {}
        day_obj = publication_date.get('day') or {}
        day_value = day_obj.get('value')
        
        if day_value and day_value.isdigit():
            day_int = int(day_value)
            if 1 <= day_int <= 31:  # Validación básica
                return day_int
        return None
    
    @staticmethod
    def _extract_doi(work):
        """Extrae el DOI de la publicación"""
        if not work:
            return None
            
        external_ids_obj = work.get('external-ids', {}) or {}
        external_ids = external_ids_obj.get('external-id', []) or []
        
        for ext_id in external_ids:
            if ext_id.get('external-id-type') == 'doi':
                return ext_id.get('external-id-value', '')
        return None
    
    @staticmethod
    def _extract_url(work):
        """Extrae la URL de la publicación"""
        if not work:
            return None
            
        # Primero buscamos URLs explícitas
        external_ids_obj = work.get('external-ids', {}) or {}
        external_ids = external_ids_obj.get('external-id', []) or []
        
        for ext_id in external_ids:
            if ext_id.get('external-id-type') == 'url':
                return ext_id.get('external-id-value', '')
        
        # Si no hay URL explícita, intentamos construir una a partir del DOI
        doi = OrcidService._extract_doi(work)
        if doi:
            return f"https://doi.org/{doi}"
        
        return None
    
    @staticmethod
    def _get_default_country():
        """Obtiene un país por defecto para journals/conferencias"""
        from app.models import Country
        # Intentamos obtener un país existente
        country = Country.query.first()
        
        # Si no hay países, creamos uno por defecto
        if not country:
            try:
                country = Country(
                    name="Sin especificar",
                    code="ZZ"
                )
                db.session.add(country)
                db.session.flush()
            except Exception as e:
                logger.error(f"Error creating default country: {str(e)}")
                return None
                
        return country