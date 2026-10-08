from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Customer, Lead, Opportunity, FollowUp
from app.crm.routes import get_scoped_query

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Scoped Queries based on user role
    customers_q = get_scoped_query(Customer, 'owner_id')
    leads_q = get_scoped_query(Lead, 'assigned_to_id')
    opps_q = get_scoped_query(Opportunity, 'owner_id')
    followups_q = get_scoped_query(FollowUp, 'assigned_to_id')

    # KPI Calculations
    total_customers = customers_q.count()
    total_leads = leads_q.count()
    open_leads = leads_q.filter(Lead.status.in_(['New', 'Contacted', 'Qualified'])).count()

    total_opps = opps_q.count()
    open_opps = opps_q.filter(Opportunity.status == 'Open').count()
    won_opps = opps_q.filter(Opportunity.status == 'Won').count()
    lost_opps = opps_q.filter(Opportunity.status == 'Lost').count()

    open_opps_list = opps_q.filter(Opportunity.status == 'Open').all()
    total_pipeline_value = sum(o.amount for o in open_opps_list)

    # Chart.js Data Preparation
    # 1. Lead Status Data
    lead_statuses = ['New', 'Contacted', 'Qualified', 'Unqualified', 'Converted', 'Lost']
    all_leads = leads_q.all()
    lead_status_counts = [sum(1 for l in all_leads if l.status == s) for s in lead_statuses]

    # 2. Opportunity Pipeline Data
    pipeline_stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']
    all_opps = opps_q.all()
    pipeline_amounts = [sum(o.amount for o in all_opps if o.stage == stage) for stage in pipeline_stages]

    # Upcoming Follow-ups
    upcoming_followups = followups_q.filter(FollowUp.status == 'Planned').order_by(FollowUp.followup_date.asc()).limit(5).all()

    kpis = {
        'total_customers': total_customers,
        'total_leads': total_leads,
        'open_leads': open_leads,
        'total_opportunities': total_opps,
        'open_opportunities': open_opps,
        'won_opportunities': won_opps,
        'lost_opportunities': lost_opps,
        'total_pipeline_value': total_pipeline_value
    }

    charts = {
        'lead_statuses': lead_statuses,
        'lead_counts': lead_status_counts,
        'pipeline_stages': pipeline_stages,
        'pipeline_amounts': pipeline_amounts
    }

    return render_template('dashboard.html', kpis=kpis, charts=charts, upcoming_followups=upcoming_followups)

@main_bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'application': 'AcxiomCRM',
        'step': 'Full Application Active',
        'framework': 'Flask'
    })
