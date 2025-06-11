// Global variables
let campaignChart = null;
let industryChart = null;

// Page Navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const pageId = e.currentTarget.dataset.page;
        
        // Update active page
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(pageId).classList.add('active');
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        e.currentTarget.classList.add('active');
        
        // Load page data
        loadPageData(pageId);
    });
});

// Load page data
async function loadPageData(pageId) {
    switch(pageId) {
        case 'dashboard':
            await loadDashboardData();
            break;
        case 'leads':
            await loadLeadsData();
            break;
        case 'campaigns':
            await loadCampaignsData();
            break;
        case 'analytics':
            await loadAnalyticsData();
            break;
    }
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        document.getElementById('total-leads').textContent = data.total_leads;
        document.getElementById('active-campaigns').textContent = data.active_campaigns;
        document.getElementById('open-rate').textContent = `${data.open_rate}%`;
        document.getElementById('response-rate').textContent = `${data.response_rate}%`;
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Leads Functions
async function loadLeadsData() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        
        const tbody = document.getElementById('leads-table');
        tbody.innerHTML = '';
        
        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${lead.name}</td>
                <td>${lead.company}</td>
                <td>${lead.industry}</td>
                <td>${lead.position}</td>
                <td><span class="badge bg-${getStatusColor(lead.status)}">${lead.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewLead(${lead.id})">
                        <i class='bx bx-show'></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteLead(${lead.id})">
                        <i class='bx bx-trash'></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error loading leads data:', error);
    }
}

// Campaign Functions
async function loadCampaignsData() {
    try {
        const response = await fetch('/api/campaigns');
        const campaigns = await response.json();
        
        const grid = document.getElementById('campaigns-grid');
        grid.innerHTML = '';
        
        campaigns.forEach(campaign => {
            const card = document.createElement('div');
            card.className = 'campaign-card';
            card.innerHTML = `
                <h3>${campaign.name}</h3>
                <p>${campaign.description || 'No description'}</p>
                <div class="campaign-stats">
                    <div class="stat-item">
                        <div class="stat-value">${campaign.total_leads}</div>
                        <div class="stat-label">Total Leads</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${campaign.response_rate}%</div>
                        <div class="stat-label">Response Rate</div>
                    </div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-sm btn-primary" onclick="startCampaign(${campaign.id})">
                        <i class='bx bx-play'></i> Start
                    </button>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewCampaign(${campaign.id})">
                        <i class='bx bx-show'></i> View
                    </button>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading campaigns data:', error);
    }
}

// Analytics Functions
async function loadAnalyticsData() {
    try {
        const [campaignResponse, industryResponse] = await Promise.all([
            fetch('/api/analytics/campaign-performance'),
            fetch('/api/analytics/industry-performance')
        ]);
        
        const campaignData = await campaignResponse.json();
        const industryData = await industryResponse.json();
        
        updateCampaignChart(campaignData);
        updateIndustryChart(industryData);
    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

function updateCampaignChart(data) {
    const ctx = document.getElementById('campaignChart').getContext('2d');
    
    if (campaignChart) {
        campaignChart.destroy();
    }
    
    campaignChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Open Rate',
                    data: data.open_rates,
                    borderColor: '#0d6efd',
                    tension: 0.4
                },
                {
                    label: 'Response Rate',
                    data: data.response_rates,
                    borderColor: '#198754',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function updateIndustryChart(data) {
    const ctx = document.getElementById('industryChart').getContext('2d');
    
    if (industryChart) {
        industryChart.destroy();
    }
    
    industryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.industries,
            datasets: [
                {
                    label: 'Response Rate',
                    data: data.response_rates,
                    backgroundColor: '#0d6efd'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Form Handlers
document.getElementById('uploadLeadsBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('leadsFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/leads/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            alert('Leads uploaded successfully');
            bootstrap.Modal.getInstance(document.getElementById('uploadLeadsModal')).hide();
            loadLeadsData();
        } else {
            const error = await response.json();
            alert(error.message || 'Error uploading leads');
        }
    } catch (error) {
        console.error('Error uploading leads:', error);
        alert('Error uploading leads');
    }
});

document.getElementById('createCampaignBtn').addEventListener('click', async () => {
    const name = document.getElementById('campaignName').value;
    const description = document.getElementById('campaignDescription').value;
    const messageTemplate = document.getElementById('messageTemplate').value;
    const frequency = document.getElementById('campaignFrequency').value;
    
    if (!name || !messageTemplate || !frequency) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/campaigns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                description,
                message_template: messageTemplate,
                frequency
            })
        });
        
        if (response.ok) {
            alert('Campaign created successfully');
            bootstrap.Modal.getInstance(document.getElementById('createCampaignModal')).hide();
            loadCampaignsData();
        } else {
            const error = await response.json();
            alert(error.message || 'Error creating campaign');
        }
    } catch (error) {
        console.error('Error creating campaign:', error);
        alert('Error creating campaign');
    }
});

// Utility Functions
function getStatusColor(status) {
    switch(status.toLowerCase()) {
        case 'new':
            return 'primary';
        case 'sent':
            return 'info';
        case 'opened':
            return 'warning';
        case 'responded':
            return 'success';
        default:
            return 'secondary';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPageData('dashboard');
}); 