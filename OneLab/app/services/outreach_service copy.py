import os
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app import db
from app.models import Lead, Campaign, CampaignLead, FollowUp
import boto3
import json

class OutreachService:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_PASSWORD')
        self.outlook_user = os.getenv('OUTLOOK_USER')
        self.outlook_password = os.getenv('OUTLOOK_PASSWORD')
        
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
    
    def generate_email_content(self, lead, campaign):
        """Generate personalized email content using Groq"""
        prompt = f"""
        Generate a personalized B2B outreach email for {lead.name} at {lead.company}.
        
        Context:
        - Industry: {lead.industry}
        - Position: {lead.position}
        - Campaign Template: {campaign.message_template}
        
        Requirements:
        1. Professional and engaging tone
        2. Personalized to their industry and role
        3. Include a clear value proposition
        4. End with a specific call to action
        5. Keep the email concise (max 3-4 paragraphs)
        6. Include a compelling subject line
        
        Format the response as JSON with 'subject' and 'body' fields.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="ollama-3.3-70b",
                messages=[
                    {"role": "system", "content": "You are a professional B2B sales outreach expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse the response as JSON
            content = json.loads(response.choices[0].message.content)
            return content
            
        except Exception as e:
            print(f"Error generating email content: {str(e)}")
            return {
                "subject": f"Exciting Business Opportunity for {lead.company}",
                "body": campaign.message_template
            }
    
    def send_email(self, lead, campaign, content, email_provider='gmail'):
        """Send email using Gmail or Outlook SMTP"""
        msg = MIMEMultipart()
        msg["Subject"] = content["subject"]
        msg["From"] = self.gmail_user if email_provider == 'gmail' else self.outlook_user
        msg["To"] = lead.email
        
        msg.attach(MIMEText(content["body"], "html"))
        
        try:
            if email_provider == 'gmail':
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(self.gmail_user, self.gmail_password)
                    server.send_message(msg)
            else:  # outlook
                with smtplib.SMTP("smtp.office365.com", 587) as server:
                    server.starttls()
                    server.login(self.outlook_user, self.outlook_password)
                    server.send_message(msg)
            
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
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_linkedin_message(self, lead, campaign, content):
        """Send LinkedIn message (placeholder for LinkedIn API integration)"""
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
            channels = ["email", "linkedin"]
        
        lead = Lead.query.get_or_404(lead_id)
        campaign = Campaign.query.get_or_404(campaign_id)
        
        # Generate content
        content = self.generate_email_content(lead, campaign)
        
        results = {
            "email_sent": False,
            "linkedin_sent": False,
            "followup_scheduled": False
        }
        
        # Send through specified channels
        if "email" in channels:
            results["email_sent"] = self.send_email(lead, campaign, content, email_provider)
        
        if "linkedin" in channels:
            results["linkedin_sent"] = self.send_linkedin_message(lead, campaign, content)
        
        # Schedule follow-up if any channel was successful
        if results["email_sent"] or results["linkedin_sent"]:
            results["followup_scheduled"] = self.schedule_followup(lead, campaign)
        
        return results 