from flask import render_template, request
from flask_login import login_required, current_user
from app.reports import reports_bp
from app.models import Customer, Lead, Opportunity, FollowUp, AuditLog
from app.crm.routes import get_scoped_query

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/customers')
@login_required
def customer_report():
    customers = get_scoped_query(Customer, 'owner_id').all()
    return render_template('reports/customer_report.html', customers=customers)

@reports_bp.route('/leads')
@login_required
def lead_report():
    leads = get_scoped_query(Lead, 'assigned_to_id').all()
    return render_template('reports/lead_report.html', leads=leads)

@reports_bp.route('/pipeline')
@login_required
def pipeline_report():
    opportunities = get_scoped_query(Opportunity, 'owner_id').all()

    stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']
    pipeline_data = {s: {'count': 0, 'amount': 0.0, 'weighted': 0.0} for s in stages}

    for opp in opportunities:
        if opp.stage in pipeline_data:
            pipeline_data[opp.stage]['count'] += 1
            pipeline_data[opp.stage]['amount'] += opp.amount
            pipeline_data[opp.stage]['weighted'] += opp.weighted_amount

    return render_template('reports/pipeline_report.html', pipeline_data=pipeline_data, opportunities=opportunities)
