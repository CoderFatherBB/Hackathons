from app import db
from datetime import datetime

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    company = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    position = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    linkedin_url = db.Column(db.String(200))
    website = db.Column(db.String(200))
    source = db.Column(db.String(50), default='manual')  # manual, hubspot, linkedin, web_scraping
    status = db.Column(db.String(50), default='new')
    last_contacted = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    message_template = db.Column(db.Text)
    frequency = db.Column(db.String(50))  # daily, weekly, monthly
    status = db.Column(db.String(50), default='draft')  # draft, active, paused, completed
    channels = db.Column(db.String(100), default='email')  # email, linkedin, or both
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, sent, opened, responded
    sent_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    responded_at = db.Column(db.DateTime)
    message_id = db.Column(db.String(100))  # For tracking email/LinkedIn message IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    emails_sent = db.Column(db.Integer, default=0)
    emails_opened = db.Column(db.Integer, default=0)
    emails_clicked = db.Column(db.Integer, default=0)
    linkedin_messages_sent = db.Column(db.Integer, default=0)
    linkedin_messages_opened = db.Column(db.Integer, default=0)
    linkedin_messages_responded = db.Column(db.Integer, default=0)
    responses_received = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    original_message_id = db.Column(db.String(100))
    status = db.Column(db.String(50), default='scheduled')  # scheduled, sent, responded
    scheduled_for = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime)
    message_content = db.Column(db.Text)  # Store the follow-up message content
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 