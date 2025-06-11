from flask import Blueprint, request, jsonify
from app import db
from app.models import Campaign, CampaignLead, Analytics, Lead, FollowUp
from datetime import datetime, timedelta
from sqlalchemy import func, case

bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@bp.route('/campaign/<int:campaign_id>', methods=['GET'])
def get_campaign_analytics(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get campaign leads statistics
    total_leads = CampaignLead.query.filter_by(campaign_id=campaign_id).count()
    sent_leads = CampaignLead.query.filter_by(
        campaign_id=campaign_id,
        status='sent'
    ).count()
    opened_leads = CampaignLead.query.filter_by(
        campaign_id=campaign_id,
        status='opened'
    ).count()
    responded_leads = CampaignLead.query.filter_by(
        campaign_id=campaign_id,
        status='responded'
    ).count()
    
    # Calculate rates
    open_rate = (opened_leads / sent_leads * 100) if sent_leads > 0 else 0
    response_rate = (responded_leads / sent_leads * 100) if sent_leads > 0 else 0
    
    # Get daily analytics
    daily_stats = db.session.query(
        func.date(CampaignLead.sent_at).label('date'),
        func.count(CampaignLead.id).label('sent'),
        func.sum(case((CampaignLead.status == 'opened', 1), else_=0)).label('opened'),
        func.sum(case((CampaignLead.status == 'responded', 1), else_=0)).label('responded')
    ).filter(
        CampaignLead.campaign_id == campaign_id,
        CampaignLead.sent_at.isnot(None)
    ).group_by(
        func.date(CampaignLead.sent_at)
    ).all()
    
    daily_analytics = [{
        'date': stat.date.isoformat(),
        'sent': stat.sent,
        'opened': stat.opened or 0,
        'responded': stat.responded or 0
    } for stat in daily_stats]
    
    return jsonify({
        'campaign_id': campaign_id,
        'campaign_name': campaign.name,
        'total_leads': total_leads,
        'sent_leads': sent_leads,
        'opened_leads': opened_leads,
        'responded_leads': responded_leads,
        'open_rate': round(open_rate, 2),
        'response_rate': round(response_rate, 2),
        'daily_analytics': daily_analytics
    })

@bp.route('/campaign/<int:campaign_id>/leads', methods=['GET'])
def get_campaign_lead_analytics(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get lead-level analytics
    lead_stats = db.session.query(
        CampaignLead.lead_id,
        Lead.name,
        Lead.company,
        Lead.industry,
        CampaignLead.status,
        CampaignLead.sent_at,
        CampaignLead.opened_at,
        CampaignLead.responded_at
    ).join(
        Lead, CampaignLead.lead_id == Lead.id
    ).filter(
        CampaignLead.campaign_id == campaign_id
    ).all()
    
    lead_analytics = [{
        'lead_id': stat.lead_id,
        'name': stat.name,
        'company': stat.company,
        'industry': stat.industry,
        'status': stat.status,
        'sent_at': stat.sent_at.isoformat() if stat.sent_at else None,
        'opened_at': stat.opened_at.isoformat() if stat.opened_at else None,
        'responded_at': stat.responded_at.isoformat() if stat.responded_at else None
    } for stat in lead_stats]
    
    return jsonify({
        'campaign_id': campaign_id,
        'campaign_name': campaign.name,
        'lead_analytics': lead_analytics
    })

@bp.route('/industry-performance', methods=['GET'])
def get_industry_performance():
    # Get performance metrics by industry
    industry_stats = db.session.query(
        Lead.industry,
        func.count(CampaignLead.id).label('total_leads'),
        func.sum(case((CampaignLead.status == 'opened', 1), else_=0)).label('opened'),
        func.sum(case((CampaignLead.status == 'responded', 1), else_=0)).label('responded')
    ).join(
        CampaignLead, Lead.id == CampaignLead.lead_id
    ).group_by(
        Lead.industry
    ).all()
    
    industry_analytics = [{
        'industry': stat.industry,
        'total_leads': stat.total_leads,
        'opened': stat.opened or 0,
        'responded': stat.responded or 0,
        'open_rate': round((stat.opened or 0) / stat.total_leads * 100, 2) if stat.total_leads > 0 else 0,
        'response_rate': round((stat.responded or 0) / stat.total_leads * 100, 2) if stat.total_leads > 0 else 0
    } for stat in industry_stats]
    
    return jsonify({
        'industry_analytics': industry_analytics
    })

@bp.route('/campaign/<int:campaign_id>/followups', methods=['GET'])
def get_campaign_followup_analytics(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get follow-up statistics
    followup_stats = db.session.query(
        func.count(FollowUp.id).label('total_followups'),
        func.sum(case((FollowUp.status == 'sent', 1), else_=0)).label('sent'),
        func.sum(case((FollowUp.status == 'responded', 1), else_=0)).label('responded')
    ).filter(
        FollowUp.campaign_id == campaign_id
    ).first()
    
    return jsonify({
        'campaign_id': campaign_id,
        'campaign_name': campaign.name,
        'total_followups': followup_stats.total_followups or 0,
        'sent_followups': followup_stats.sent or 0,
        'responded_followups': followup_stats.responded or 0,
        'followup_response_rate': round(
            (followup_stats.responded or 0) / (followup_stats.sent or 1) * 100,
            2
        )
    }) 