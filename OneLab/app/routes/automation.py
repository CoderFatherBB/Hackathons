from flask import Blueprint, request, jsonify
from app import db
from app.models import Lead, Campaign, CampaignLead, FollowUp
from app.services.outreach_service import OutreachService
from datetime import datetime, timedelta
import os
import json

bp = Blueprint('automation', __name__, url_prefix='/api/automation')

# Initialize outreach service
outreach_service = OutreachService()

@bp.route('/generate-message', methods=['POST'])
def generate_message():
    """Generate and preview email content without sending"""
    data = request.get_json()
    lead_id = data.get('lead_id')
    campaign_id = data.get('campaign_id')
    
    lead = Lead.query.get_or_404(lead_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    
    try:
        content = outreach_service.generate_email_content(lead, campaign)
        return jsonify({
            'message': content,
            'lead': {
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'company': lead.company
            },
            'campaign': {
                'id': campaign.id,
                'name': campaign.name
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/send-email', methods=['POST'])
def send_email():
    """Send email after user confirmation"""
    data = request.get_json()
    lead_id = data.get('lead_id')
    campaign_id = data.get('campaign_id')
    content = data.get('content')  # The AI-generated content to send
    
    try:
        # Create campaign lead record if it doesn't exist
        campaign_lead = CampaignLead.query.filter_by(
            campaign_id=campaign_id,
            lead_id=lead_id
        ).first()
        
        if not campaign_lead:
            campaign_lead = CampaignLead(
                campaign_id=campaign_id,
                lead_id=lead_id,
                status='pending'
            )
            db.session.add(campaign_lead)
            db.session.commit()
        
        # Send the email
        results = outreach_service.process_outreach(
            lead_id=lead_id,
            campaign_id=campaign_id,
            channels=['email'],
            email_provider='gmail'
        )
        
        if results['email_sent']:
            return jsonify({
                'message': 'Email sent successfully',
                'followup_scheduled': results['followup_scheduled']
            })
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/send-linkedin-message', methods=['POST'])
def send_linkedin_message():
    data = request.get_json()
    lead_id = data.get('lead_id')
    campaign_id = data.get('campaign_id')
    message = data.get('message')
    
    try:
        results = outreach_service.process_outreach(
            lead_id=lead_id,
            campaign_id=campaign_id,
            channels=['linkedin']
        )
        
        if results['linkedin_sent']:
            return jsonify({
                'message': 'LinkedIn message sent successfully',
                'followup_scheduled': results['followup_scheduled']
            })
        else:
            return jsonify({'error': 'Failed to send LinkedIn message'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/send-all', methods=['POST'])
def send_all_messages():
    """Send emails to all leads in a campaign"""
    data = request.get_json()
    campaign_id = data.get('campaign_id')
    
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign_leads = CampaignLead.query.filter_by(
        campaign_id=campaign_id,
        status='pending'
    ).all()
    
    results = {
        'total': len(campaign_leads),
        'sent': 0,
        'failed': 0,
        'followups_scheduled': 0
    }
    
    for campaign_lead in campaign_leads:
        try:
            # Generate content for each lead
            lead = Lead.query.get(campaign_lead.lead_id)
            content = outreach_service.generate_email_content(lead, campaign)
            
            # Send the email
            lead_results = outreach_service.process_outreach(
                lead_id=lead.id,
                campaign_id=campaign_id,
                channels=['email'],
                email_provider='gmail'
            )
            
            if lead_results['email_sent']:
                results['sent'] += 1
                if lead_results['followup_scheduled']:
                    results['followups_scheduled'] += 1
            else:
                results['failed'] += 1
                
        except Exception as e:
            print(f"Error processing lead {campaign_lead.lead_id}: {str(e)}")
            results['failed'] += 1
    
    return jsonify(results)

@bp.route('/schedule-followup', methods=['POST'])
def schedule_followup():
    data = request.get_json()
    lead_id = data.get('lead_id')
    campaign_id = data.get('campaign_id')
    days = data.get('days', 3)
    
    lead = Lead.query.get_or_404(lead_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    
    try:
        followup_date = datetime.utcnow() + timedelta(days=days)
        
        followup = FollowUp(
            lead_id=lead_id,
            campaign_id=campaign_id,
            scheduled_for=followup_date
        )
        db.session.add(followup)
        db.session.commit()
        
        # Trigger AWS Lambda function
        payload = {
            'followup_id': followup.id,
            'lead_id': lead_id,
            'campaign_id': campaign_id,
            'scheduled_for': followup_date.isoformat()
        }
        
        outreach_service.lambda_client.invoke(
            FunctionName='FollowupEmailLambda',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        return jsonify({
            'message': 'Follow-up scheduled successfully',
            'scheduled_for': followup_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/check-followups', methods=['GET'])
def check_followups():
    """Check for pending follow-ups"""
    current_time = datetime.utcnow()
    pending_followups = FollowUp.query.filter(
        FollowUp.status == 'scheduled',
        FollowUp.scheduled_for <= current_time
    ).all()
    
    results = []
    for followup in pending_followups:
        try:
            lead = Lead.query.get(followup.lead_id)
            campaign = Campaign.query.get(followup.campaign_id)
            
            # Process follow-up
            lead_results = outreach_service.process_outreach(
                lead_id=lead.id,
                campaign_id=campaign.id,
                channels=['email'],
                email_provider='gmail'
            )
            
            if lead_results['email_sent']:
                followup.status = 'sent'
                followup.sent_at = datetime.utcnow()
                db.session.commit()
                
                results.append({
                    'followup_id': followup.id,
                    'lead_id': lead.id,
                    'campaign_id': campaign.id,
                    'status': 'sent'
                })
            else:
                results.append({
                    'followup_id': followup.id,
                    'lead_id': lead.id,
                    'campaign_id': campaign.id,
                    'status': 'failed'
                })
                
        except Exception as e:
            print(f"Error processing follow-up {followup.id}: {str(e)}")
            results.append({
                'followup_id': followup.id,
                'error': str(e)
            })
    
    return jsonify({
        'total_checked': len(pending_followups),
        'results': results
    }) 