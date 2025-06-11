from app import create_app, db
from app.models import Campaign, Lead, CampaignLead
from datetime import datetime

def seed_database():
    app = create_app()
    with app.app_context():
        # Clear existing data
        CampaignLead.query.delete()
        Lead.query.delete()
        Campaign.query.delete()
        
        # Create campaigns
        campaigns = [
            Campaign(
                name="Tech Industry Outreach",
                description="Targeting technology companies for our AI solutions",
                message_template="Hi {name},\n\nI noticed you're working at {company} in the {industry} industry. Our AI solutions have helped similar companies improve their efficiency by 40%.\n\nWould you be interested in a brief demo of how we could help {company}?\n\nBest regards,\nYour Name",
                frequency="weekly",
                status="active"
            ),
            Campaign(
                name="Healthcare Solutions",
                description="Reaching out to healthcare providers about our compliance solutions",
                message_template="Hi {name},\n\nI see you're the {position} at {company}. Our healthcare compliance solutions have helped similar organizations streamline their processes and reduce risks.\n\nWould you be open to a 15-minute call to discuss how we could help {company}?\n\nBest regards,\nYour Name",
                frequency="monthly",
                status="active"
            ),
            Campaign(
                name="Startup Growth Program",
                description="Targeting startups for our growth acceleration program",
                message_template="Hi {name},\n\nI noticed {company} is making waves in the {industry} space. Our startup growth program has helped similar companies scale their operations efficiently.\n\nWould you be interested in learning more about how we could help {company} accelerate its growth?\n\nBest regards,\nYour Name",
                frequency="daily",
                status="active"
            )
        ]
        
        for campaign in campaigns:
            db.session.add(campaign)
        db.session.commit()
        
        # Create leads
        leads = [
            Lead(
                name="John Smith",
                email="john.smith@techcorp.com",
                company="TechCorp Solutions",
                industry="Technology",
                position="CTO",
                status="new"
            ),
            Lead(
                name="Sarah Johnson",
                email="sarah.j@healthcareplus.com",
                company="Healthcare Plus",
                industry="Healthcare",
                position="Operations Director",
                status="new"
            ),
            Lead(
                name="Michael Chen",
                email="michael@innovatech.com",
                company="InnovaTech",
                industry="Technology",
                position="CEO",
                status="new"
            ),
            Lead(
                name="Emily Brown",
                email="emily.b@fintech.com",
                company="FinTech Solutions",
                industry="Financial Services",
                position="Head of Innovation",
                status="new"
            ),
            Lead(
                name="David Wilson",
                email="david.w@manufacturepro.com",
                company="ManufacturePro",
                industry="Manufacturing",
                position="Operations Manager",
                status="new"
            )
        ]
        
        for lead in leads:
            db.session.add(lead)
        db.session.commit()
        
        # Associate leads with campaigns
        for lead in leads:
            for campaign in campaigns:
                campaign_lead = CampaignLead(
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                    status="pending"
                )
                db.session.add(campaign_lead)
        
        db.session.commit()
        print("Sample data has been added to the database successfully!")

if __name__ == "__main__":
    seed_database() 