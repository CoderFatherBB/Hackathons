from flask import Blueprint, request, jsonify
from app import db
from app.models import Lead
from app.services.lead_generator import LeadGenerator
import csv
from werkzeug.utils import secure_filename
import os

bp = Blueprint('leads', __name__, url_prefix='/api/leads')

@bp.route('/generate', methods=['POST'])
def generate_leads():
    """Generate leads from multiple sources"""
    data = request.get_json()
    sources = data.get('sources', ['hubspot', 'linkedin', 'web'])
    website_url = data.get('website_url')
    
    generator = LeadGenerator()
    result = generator.generate_leads(sources=sources, website_url=website_url)
    
    return jsonify(result)

@bp.route('/upload', methods=['POST'])
def upload_leads():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            leads_added = 0
            with open(filepath, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Check if lead already exists
                    existing_lead = Lead.query.filter_by(email=row.get('email')).first()
                    
                    if not existing_lead:
                        lead = Lead(
                            name=row.get('name'),
                            email=row.get('email'),
                            company=row.get('company'),
                            industry=row.get('industry'),
                            position=row.get('position'),
                            phone=row.get('phone'),
                            website=row.get('website'),
                            linkedin_url=row.get('linkedin_url'),
                            source='manual'
                        )
                        db.session.add(lead)
                        leads_added += 1
            
            db.session.commit()
            os.remove(filepath)  # Clean up uploaded file
            
            return jsonify({
                'message': f'{leads_added} leads uploaded successfully',
                'total_leads': leads_added
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file format. Only CSV files are supported.'}), 400

@bp.route('/', methods=['GET'])
def get_leads():
    leads = Lead.query.all()
    return jsonify([{
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'company': lead.company,
        'industry': lead.industry,
        'position': lead.position,
        'phone': lead.phone,
        'website': lead.website,
        'linkedin_url': lead.linkedin_url,
        'source': lead.source,
        'status': lead.status,
        'last_contacted': lead.last_contacted.isoformat() if lead.last_contacted else None,
        'created_at': lead.created_at.isoformat()
    } for lead in leads])

@bp.route('/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return jsonify({
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'company': lead.company,
        'industry': lead.industry,
        'position': lead.position,
        'phone': lead.phone,
        'website': lead.website,
        'linkedin_url': lead.linkedin_url,
        'source': lead.source,
        'status': lead.status,
        'last_contacted': lead.last_contacted.isoformat() if lead.last_contacted else None,
        'created_at': lead.created_at.isoformat()
    })

@bp.route('/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(lead, key):
            setattr(lead, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Lead updated successfully'})

@bp.route('/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    return jsonify({'message': 'Lead deleted successfully'})

@bp.route('/sources', methods=['GET'])
def get_lead_sources():
    """Get available lead sources and their status"""
    return jsonify({
        'sources': [
            {
                'name': 'HubSpot',
                'enabled': bool(os.getenv('HUBSPOT_API_KEY')),
                'description': 'Import leads from HubSpot CRM'
            },
            {
                'name': 'LinkedIn',
                'enabled': bool(os.getenv('LINKEDIN_API_KEY')),
                'description': 'Import leads from LinkedIn Sales Navigator'
            },
            {
                'name': 'Web Scraping',
                'enabled': True,
                'description': 'Extract leads from business websites'
            }
        ]
    }) 