import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime
import os
from app import db
from app.models import Lead

class LeadGenerator:
    def __init__(self):
        self.hubspot_token = os.getenv('HUBSPOT_API_KEY')
        self.linkedin_key = os.getenv('LINKEDIN_API_KEY')
        self.linkedin_secret = os.getenv('LINKEDIN_API_SECRET')
        
    def fetch_hubspot_leads(self):
        """Fetch leads from HubSpot CRM"""
        hubspot_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        headers = {
            "Authorization": f"Bearer {self.hubspot_token}",
            "Content-Type": "application/json"
        }
        params = {
            "properties": "firstname,lastname,email,company,phone,industry,position",
            "limit": 100
        }
        
        hubspot_data = []
        while hubspot_url:
            response = requests.get(hubspot_url, headers=headers, params=params).json()
            
            for item in response.get("results", []):
                properties = item.get("properties", {})
                hubspot_data.append({
                    "name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
                    "email": properties.get("email", ""),
                    "company": properties.get("company", ""),
                    "industry": properties.get("industry", ""),
                    "position": properties.get("position", ""),
                    "phone": properties.get("phone", ""),
                    "source": "hubspot"
                })
            
            # Handle pagination
            hubspot_url = response.get("paging", {}).get("next", {}).get("link")
        
        return hubspot_data
    
    def fetch_linkedin_leads(self):
        """Fetch leads from LinkedIn Sales Navigator"""
        # LinkedIn API implementation would go here
        # This is a placeholder for the actual LinkedIn API integration
        linkedin_data = []
        return linkedin_data
    
    def scrape_website_leads(self, url):
        """Scrape leads from a business website"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            leads = []
            
            # Example selectors - adjust based on target website structure
            for item in soup.select(".lead-item, .contact-info, .team-member"):
                lead = {
                    "name": "",
                    "email": "",
                    "company": "",
                    "industry": "",
                    "position": "",
                    "source": "web_scraping"
                }
                
                # Extract name
                name_elem = item.select_one(".name, h3, .title")
                if name_elem:
                    lead["name"] = name_elem.text.strip()
                
                # Extract email
                email_elem = item.select_one(".email, a[href^='mailto:']")
                if email_elem:
                    lead["email"] = email_elem.text.strip() or email_elem.get("href", "").replace("mailto:", "")
                
                # Extract company
                company_elem = item.select_one(".company, .organization")
                if company_elem:
                    lead["company"] = company_elem.text.strip()
                
                # Extract position
                position_elem = item.select_one(".position, .role")
                if position_elem:
                    lead["position"] = position_elem.text.strip()
                
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            print(f"Error scraping website: {str(e)}")
            return []
    
    def save_leads_to_database(self, leads):
        """Save leads to database"""
        for lead_data in leads:
            # Check if lead already exists
            existing_lead = Lead.query.filter_by(email=lead_data["email"]).first()
            
            if not existing_lead:
                lead = Lead(
                    name=lead_data["name"],
                    email=lead_data["email"],
                    company=lead_data["company"],
                    industry=lead_data["industry"],
                    position=lead_data["position"],
                    source=lead_data.get("source", "manual")
                )
                db.session.add(lead)
        
        db.session.commit()
    
    def generate_csv(self, leads, filename=None):
        """Generate CSV file from leads data"""
        if not filename:
            filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['name', 'email', 'company', 'industry', 'position', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lead in leads:
                writer.writerow(lead)
        
        return filename
    
    def generate_leads(self, sources=None, website_url=None):
        """Generate leads from specified sources"""
        all_leads = []
        
        if not sources:
            sources = ["hubspot", "linkedin", "web"]
        
        if "hubspot" in sources:
            hubspot_leads = self.fetch_hubspot_leads()
            all_leads.extend(hubspot_leads)
        
        if "linkedin" in sources:
            linkedin_leads = self.fetch_linkedin_leads()
            all_leads.extend(linkedin_leads)
        
        if "web" in sources and website_url:
            web_leads = self.scrape_website_leads(website_url)
            all_leads.extend(web_leads)
        
        # Save to database
        self.save_leads_to_database(all_leads)
        
        # Generate CSV
        csv_file = self.generate_csv(all_leads)
        
        return {
            "total_leads": len(all_leads),
            "csv_file": csv_file,
            "leads": all_leads
        } 