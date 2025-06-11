from flask import Blueprint, request, jsonify
from app import db
from app.models import Campaign, CampaignLead, Lead
from datetime import datetime

bp = Blueprint('campaigns', __name__, url_prefix='/api/campaigns')

@bp.route('/', methods=['POST'])
def create_campaign():
    data = request.get_json()
    
    campaign = Campaign(
        name=data['name'],
        description=data.get('description'),
        message_template=data['message_template'],
        frequency=data['frequency']
    )
    
    db.session.add(campaign)
    db.session.commit()
    
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'message_template': campaign.message_template,
        'frequency': campaign.frequency,
        'status': campaign.status,
        'created_at': campaign.created_at.isoformat()
    }), 201

@bp.route('/', methods=['GET'])
def get_campaigns():
    campaigns = Campaign.query.all()
    return jsonify([{
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'message_template': campaign.message_template,
        'frequency': campaign.frequency,
        'status': campaign.status,
        'created_at': campaign.created_at.isoformat()
    } for campaign in campaigns])

@bp.route('/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'message_template': campaign.message_template,
        'frequency': campaign.frequency,
        'status': campaign.status,
        'created_at': campaign.created_at.isoformat()
    })

@bp.route('/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(campaign, key):
            setattr(campaign, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Campaign updated successfully'})

@bp.route('/<int:campaign_id>/leads', methods=['POST'])
def add_leads_to_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    data = request.get_json()
    lead_ids = data.get('lead_ids', [])
    
    for lead_id in lead_ids:
        lead = Lead.query.get_or_404(lead_id)
        campaign_lead = CampaignLead(
            campaign_id=campaign.id,
            lead_id=lead.id
        )
        db.session.add(campaign_lead)
    
    db.session.commit()
    return jsonify({'message': 'Leads added to campaign successfully'})

@bp.route('/<int:campaign_id>/leads', methods=['GET'])
def get_campaign_leads(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign_leads = CampaignLead.query.filter_by(campaign_id=campaign_id).all()
    
    leads = []
    for cl in campaign_leads:
        lead = Lead.query.get(cl.lead_id)
        leads.append({
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'company': lead.company,
            'status': cl.status,
            'sent_at': cl.sent_at.isoformat() if cl.sent_at else None,
            'opened_at': cl.opened_at.isoformat() if cl.opened_at else None,
            'responded_at': cl.responded_at.isoformat() if cl.responded_at else None
        })
    
    return jsonify(leads)

@bp.route('/<int:campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.status = 'active'
    db.session.commit()
    return jsonify({'message': 'Campaign started successfully'})

@bp.route('/<int:campaign_id>/pause', methods=['POST'])
def pause_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.status = 'paused'
    db.session.commit()
    return jsonify({'message': 'Campaign paused successfully'}) 