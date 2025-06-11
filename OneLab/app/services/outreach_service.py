import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app import db
from app.models import Lead, Campaign, CampaignLead, FollowUp
import boto3
import json
from groq import Groq

class OutreachService:
    def __init__(self):
        self.groq_client = None
        try:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {str(e)}")
            print("Message generation will use template-based approach instead.")
        
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_PASSWORD')
        
        # Optional integrations
        self.outlook_user = os.getenv('OUTLOOK_USER')
        self.outlook_password = os.getenv('OUTLOOK_PASSWORD')
        self.linkedin_key = os.getenv('LINKEDIN_API_KEY')
        self.linkedin_secret = os.getenv('LINKEDIN_API_SECRET')
        self.salesforce_key = os.getenv('SALESFORCE_API_KEY')
        
        # Initialize AWS client only if credentials are provided
        self.lambda_client = None
        if all([
            os.getenv('AWS_ACCESS_KEY_ID'),
            os.getenv('AWS_SECRET_ACCESS_KEY'),
            os.getenv('AWS_REGION')
        ]):
            self.lambda_client = boto3.client(
                'lambda',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
    
    def generate_message(self, lead, campaign):
        """Generate personalized message using Groq or template"""
        if self.groq_client:
            try:
                prompt = f"""Generate a personalized outreach message for:
                Name: {lead.name}
                Company: {lead.company}
                Industry: {lead.industry}
                Position: {lead.position}
                
                Campaign context: {campaign.description}
                Message template: {campaign.message_template}
                
                Generate a personalized message that maintains the core message but adds personalization."""
                
                response = self.groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                
                return response.choices[0].message.content
            except Exception as e:
                print(f"Warning: Groq API error: {str(e)}")
                print("Falling back to template-based message generation.")
        
        # Fallback to template-based generation
        message = campaign.message_template.format(
            name=lead.name,
            company=lead.company,
            industry=lead.industry,
            position=lead.position
        )
        return message
    
    def send_email(self, lead, campaign, email_content, email_provider='gmail'):
        """Send email using specified provider"""
        try:
            if email_provider == 'gmail':
                if not self.gmail_user or not self.gmail_password:
                    raise ValueError("Gmail credentials not configured")
                
                msg = MIMEMultipart()
                msg['From'] = self.gmail_user
                msg['To'] = lead.email
                msg['Subject'] = f"Reaching out from {campaign.name}"
                
                msg.attach(MIMEText(email_content, 'plain'))
                
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(self.gmail_user, self.gmail_password)
                    server.send_message(msg)
            
            elif email_provider == 'outlook':
                if not self.outlook_user or not self.outlook_password:
                    raise ValueError("Outlook credentials not configured")
                
                msg = MIMEMultipart()
                msg['From'] = self.outlook_user
                msg['To'] = lead.email
                msg['Subject'] = f"Reaching out from {campaign.name}"
                
                msg.attach(MIMEText(email_content, 'plain'))
                
                with smtplib.SMTP('smtp.office365.com', 587) as server:
                    server.starttls()
                    server.login(self.outlook_user, self.outlook_password)
                    server.send_message(msg)
            
            # Update lead status
            lead.status = 'contacted'
            lead.last_contacted = datetime.utcnow()
            db.session.commit()
            
            # Schedule follow-up
            follow_up = FollowUp(
                lead_id=lead.id,
                campaign_id=campaign.id,
                scheduled_for=datetime.utcnow() + timedelta(days=campaign.frequency_days),
                status='scheduled'
            )
            db.session.add(follow_up)
            db.session.commit()
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, str(e)
    
    def send_linkedin_message(self, lead, campaign, content):
        """Send LinkedIn message if API credentials are configured"""
        if not (self.linkedin_key and self.linkedin_secret):
            print("LinkedIn API credentials not configured - skipping LinkedIn message")
            return False
            
        # LinkedIn API implementation would go here
        # This is a placeholder for the actual LinkedIn API integration
        try:
            # Update campaign lead status
            campaign_lead = CampaignLead.query.filter_by(
                campaign_id=campaign.id,
                lead_id=lead.id
            ).first()
            
            if campaign_lead:
                campaign_lead.status = "sent"
                campaign_lead.sent_at = datetime.utcnow()
                db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error sending LinkedIn message: {str(e)}")
            return False
    
    def schedule_followup(self, lead, campaign):
        """Schedule follow-up using AWS Lambda or local scheduling"""
        followup_date = datetime.utcnow() + timedelta(days=3)
        
        followup = FollowUp(
            lead_id=lead.id,
            campaign_id=campaign.id,
            scheduled_for=followup_date
        )
        db.session.add(followup)
        db.session.commit()
        
        # Only use AWS Lambda if credentials are configured
        if self.lambda_client:
            try:
                payload = {
                    "followup_id": followup.id,
                    "lead_id": lead.id,
                    "campaign_id": campaign.id,
                    "scheduled_for": followup_date.isoformat()
                }
                
                self.lambda_client.invoke(
                    FunctionName="FollowupEmailLambda",
                    InvocationType="Event",
                    Payload=json.dumps(payload)
                )
                return True
            except Exception as e:
                print(f"Error scheduling follow-up with AWS Lambda: {str(e)}")
                return False
        else:
            print("AWS Lambda not configured - follow-up will be processed locally")
            return True
    
    def process_outreach(self, lead_id, campaign_id, channels=None, email_provider='gmail'):
        """Process outreach for a lead"""
        if not channels:
            channels = ["email"]  # Default to email only for demo
        
        lead = Lead.query.get_or_404(lead_id)
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Generate content
        content = self.generate_message(lead, campaign)
        
        results = {
            "email_sent": False,
            "linkedin_sent": False,
            "followup_scheduled": False,
            "generated_content": content  # Include generated content in results
        }
        
        # Send through specified channels
        if "email" in channels:
            results["email_sent"], results["email_message"] = self.send_email(lead, campaign, content, email_provider)
        
        if "linkedin" in channels and self.linkedin_key and self.linkedin_secret:
            results["linkedin_sent"] = self.send_linkedin_message(lead, campaign, content)
        
        # Schedule follow-up if any channel was successful
        if results["email_sent"] or results["linkedin_sent"]:
            results["followup_scheduled"] = self.schedule_followup(lead, campaign)
        
        return results 

    def check_followups(self):
        """Process pending follow-ups"""
        current_time = datetime.utcnow()
        pending_followups = FollowUp.query.filter(
            FollowUp.status == 'scheduled',
            FollowUp.scheduled_for <= current_time
        ).all()
        
        results = []
        for followup in pending_followups:
            lead = Lead.query.get(followup.lead_id)
            campaign = Campaign.query.get(followup.campaign_id)
            
            if lead and campaign:
                # Generate follow-up message
                message = self.generate_message(lead, campaign)
                
                # Send follow-up email
                success, message = self.send_email(lead, campaign, message)
                
                # Update follow-up status
                followup.status = 'completed' if success else 'failed'
                followup.completed_at = current_time if success else None
                followup.error_message = None if success else message
                db.session.commit()
                
                results.append({
                    'lead_id': lead.id,
                    'campaign_id': campaign.id,
                    'success': success,
                    'message': message
                })
        
        return results 