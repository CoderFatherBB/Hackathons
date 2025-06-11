import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Configure the page
st.set_page_config(
    page_title="OneLab - Lead Outreach Automation",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = []
if 'leads' not in st.session_state:
    st.session_state.leads = []

# API endpoint
API_URL = "http://localhost:5000/api"

def fetch_campaigns():
    response = requests.get(f"{API_URL}/campaigns/")
    if response.status_code == 200:
        st.session_state.campaigns = response.json()

def fetch_leads():
    response = requests.get(f"{API_URL}/leads/")
    if response.status_code == 200:
        st.session_state.leads = response.json()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Campaigns", "Leads", "Automation"])

# Main content
st.title("🚀 OneLab - Lead Outreach Automation")

if page == "Dashboard":
    st.header("Dashboard")
    
    # Fetch data
    fetch_campaigns()
    fetch_leads()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Campaigns", len(st.session_state.campaigns))
    with col2:
        st.metric("Total Leads", len(st.session_state.leads))
    with col3:
        active_leads = len([lead for lead in st.session_state.leads if lead.get('status') == 'active'])
        st.metric("Active Leads", active_leads)
    
    # Recent activity
    st.subheader("Recent Activity")
    if st.session_state.leads:
        recent_leads = pd.DataFrame(st.session_state.leads)
        recent_leads['created_at'] = pd.to_datetime(recent_leads['created_at'])
        st.dataframe(recent_leads.sort_values('created_at', ascending=False).head(5))

elif page == "Campaigns":
    st.header("Campaigns")
    
    # Create new campaign
    with st.expander("Create New Campaign"):
        with st.form("new_campaign"):
            name = st.text_input("Campaign Name")
            description = st.text_area("Description")
            message_template = st.text_area("Message Template")
            frequency = st.selectbox("Follow-up Frequency", ["daily", "weekly", "monthly"])
            
            if st.form_submit_button("Create Campaign"):
                data = {
                    "name": name,
                    "description": description,
                    "message_template": message_template,
                    "frequency": frequency
                }
                response = requests.post(f"{API_URL}/campaigns/", json=data)
                if response.status_code == 201:
                    st.success("Campaign created successfully!")
                    fetch_campaigns()
    
    # Display campaigns
    if st.session_state.campaigns:
        for campaign in st.session_state.campaigns:
            with st.container():
                st.subheader(campaign['name'])
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Description:** {campaign['description']}")
                    st.write(f"**Frequency:** {campaign['frequency']}")
                with col2:
                    if st.button("View Details", key=f"campaign_{campaign['id']}"):
                        st.write("Message Template:")
                        st.code(campaign['message_template'])

elif page == "Leads":
    st.header("Leads")
    
    # Create new lead
    with st.expander("Add New Lead"):
        with st.form("new_lead"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            company = st.text_input("Company")
            industry = st.text_input("Industry")
            position = st.text_input("Position")
            
            if st.form_submit_button("Add Lead"):
                data = {
                    "name": name,
                    "email": email,
                    "company": company,
                    "industry": industry,
                    "position": position
                }
                response = requests.post(f"{API_URL}/leads/", json=data)
                if response.status_code == 201:
                    st.success("Lead added successfully!")
                    fetch_leads()
    
    # Upload leads from CSV
    with st.expander("Upload Leads from CSV"):
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            if st.button("Upload"):
                files = {'file': uploaded_file}
                response = requests.post(f"{API_URL}/leads/upload", files=files)
                if response.status_code == 200:
                    st.success("Leads uploaded successfully!")
                    fetch_leads()
    
    # Display leads
    if st.session_state.leads:
        leads_df = pd.DataFrame(st.session_state.leads)
        st.dataframe(leads_df)

elif page == "Automation":
    st.header("Automation")
    
    # Generate and send messages
    st.subheader("Generate and Send Messages")
    
    # Select campaign and lead
    if st.session_state.campaigns and st.session_state.leads:
        campaign = st.selectbox("Select Campaign", st.session_state.campaigns, format_func=lambda x: x['name'])
        lead = st.selectbox("Select Lead", st.session_state.leads, format_func=lambda x: f"{x['name']} ({x['company']})")
        
        if st.button("Generate Message"):
            data = {
                "lead_id": lead['id'],
                "campaign_id": campaign['id']
            }
            response = requests.post(f"{API_URL}/automation/generate-message", json=data)
            if response.status_code == 200:
                generated_content = response.json()['content']
                st.text_area("Generated Message", generated_content, height=200)
                
                if st.button("Send Message"):
                    send_data = {
                        "lead_id": lead['id'],
                        "campaign_id": campaign['id'],
                        "email_content": generated_content
                    }
                    response = requests.post(f"{API_URL}/automation/send-email", json=send_data)
                    if response.status_code == 200:
                        st.success("Message sent successfully!")
    
    # Check follow-ups
    st.subheader("Pending Follow-ups")
    if st.button("Check Follow-ups"):
        response = requests.post(f"{API_URL}/automation/check-followups")
        if response.status_code == 200:
            followups = response.json()
            if followups:
                st.write("Follow-ups processed:")
                for followup in followups:
                    st.write(f"- Lead ID: {followup['lead_id']}, Success: {followup['success']}")
            else:
                st.info("No pending follow-ups to process.") 