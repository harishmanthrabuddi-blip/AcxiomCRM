from datetime import datetime, date
import uuid
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.crm import crm_bp
from app.extensions import db
from app.models import Customer, Lead, Opportunity, FollowUp, User, Activity
from app.forms import CustomerForm, LeadForm, OpportunityForm, FollowUpForm
from app.services.audit import log_audit

# Helper for scope filtering
def get_scoped_query(model, user_attr='owner_id'):
    query = model.query
    if current_user.role_name == 'Sales Executive':
        query = query.filter(getattr(model, user_attr) == current_user.id)
    return query

# ==========================================
# 1. CUSTOMER MANAGEMENT (Create, Edit, Details, Delete, Search)
# ==========================================

@crm_bp.route('/customers')
@login_required
def customers_list():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = get_scoped_query(Customer, 'owner_id')

    if search:
        query = query.filter(
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.email.ilike(f'%{search}%')) |
            (Customer.phone.ilike(f'%{search}%')) |
            (Customer.company_name.ilike(f'%{search}%'))
        )
    if status_filter:
        query = query.filter(Customer.status == status_filter)

    customers = query.order_by(Customer.created_at.desc()).all()
    return render_template('crm/customers/list.html', customers=customers, search=search, status_filter=status_filter)

@crm_bp.route('/customers/<int:id>')
@login_required
def customer_details(id):
    customer = Customer.query.get_or_404(id)
    if current_user.role_name == 'Sales Executive' and customer.owner_id != current_user.id:
        flash('Access denied: You can only view details of your assigned customers.', 'danger')
        return redirect(url_for('crm.customers_list'))
    return render_template('crm/customers/details.html', customer=customer)

@crm_bp.route('/customers/new', methods=['GET', 'POST'])
@login_required
def customer_create():
    form = CustomerForm()
    users = User.query.filter_by(is_active=True).all()
    form.owner_id.choices = [(u.id, f"{u.name} ({u.role_name})") for u in users]
    if current_user.role_name == 'Sales Executive':
        form.owner_id.data = current_user.id

    if form.validate_on_submit():
        code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
        customer = Customer(
            customer_code=code,
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
            company_name=form.company_name.data.strip() if form.company_name.data else None,
            address=form.address.data.strip() if form.address.data else None,
            city=form.city.data.strip() if form.city.data else None,
            state=form.state.data.strip() if form.state.data else None,
            status=form.status.data,
            owner_id=form.owner_id.data,
            created_by_id=current_user.id
        )
        db.session.add(customer)
        db.session.commit()

        log_audit(action='Create', entity_name='Customer', record_id=customer.id, new_value=customer.name)
        flash(f'Customer "{customer.name}" created successfully.', 'success')
        return redirect(url_for('crm.customers_list'))

    return render_template('crm/customers/form.html', form=form, title="Create Customer")

@crm_bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def customer_edit(id):
    customer = Customer.query.get_or_404(id)
    if current_user.role_name == 'Sales Executive' and customer.owner_id != current_user.id:
        flash('Access denied: You can only edit your assigned customers.', 'danger')
        return redirect(url_for('crm.customers_list'))

    form = CustomerForm(original_customer=customer, obj=customer)
    users = User.query.filter_by(is_active=True).all()
    form.owner_id.choices = [(u.id, f"{u.name} ({u.role_name})") for u in users]

    if form.validate_on_submit():
        old_val = customer.name
        customer.name = form.name.data.strip()
        customer.email = form.email.data.lower().strip()
        customer.phone = form.phone.data.strip()
        customer.company_name = form.company_name.data.strip() if form.company_name.data else None
        customer.address = form.address.data.strip() if form.address.data else None
        customer.city = form.city.data.strip() if form.city.data else None
        customer.state = form.state.data.strip() if form.state.data else None
        customer.status = form.status.data
        customer.owner_id = form.owner_id.data

        db.session.commit()
        log_audit(action='Update', entity_name='Customer', record_id=customer.id, old_value=old_val, new_value=customer.name)
        flash(f'Customer "{customer.name}" updated successfully.', 'success')
        return redirect(url_for('crm.customers_list'))

    return render_template('crm/customers/form.html', form=form, title="Edit Customer", customer=customer)

@crm_bp.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def customer_delete(id):
    customer = Customer.query.get_or_404(id)
    if current_user.role_name not in ['Admin', 'Manager']:
        flash('Access denied: Only Admins and Managers can delete customer records.', 'danger')
        return redirect(url_for('crm.customers_list'))

    name = customer.name
    db.session.delete(customer)
    db.session.commit()
    log_audit(action='Delete', entity_name='Customer', record_id=id, old_value=name)
    flash(f'Customer "{name}" has been deleted.', 'info')
    return redirect(url_for('crm.customers_list'))

# ==========================================
# 2. LEAD MANAGEMENT (Create, Edit, Details, Delete, Lead Status, Lead Conversion)
# ==========================================

@crm_bp.route('/leads')
@login_required
def leads_list():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = get_scoped_query(Lead, 'assigned_to_id')

    if search:
        query = query.filter(
            (Lead.name.ilike(f'%{search}%')) |
            (Lead.email.ilike(f'%{search}%')) |
            (Lead.phone.ilike(f'%{search}%')) |
            (Lead.company_name.ilike(f'%{search}%'))
        )
    if status_filter:
        query = query.filter(Lead.status == status_filter)

    leads = query.order_by(Lead.created_at.desc()).all()
    return render_template('crm/leads/list.html', leads=leads, search=search, status_filter=status_filter)

@crm_bp.route('/leads/<int:id>')
@login_required
def lead_details(id):
    lead = Lead.query.get_or_404(id)
    if current_user.role_name == 'Sales Executive' and lead.assigned_to_id != current_user.id:
        flash('Access denied: You can only view details of your assigned leads.', 'danger')
        return redirect(url_for('crm.leads_list'))
    return render_template('crm/leads/details.html', lead=lead)

@crm_bp.route('/leads/new', methods=['GET', 'POST'])
@login_required
def lead_create():
    form = LeadForm()
    users = User.query.filter_by(is_active=True).all()
    form.assigned_to_id.choices = [(u.id, f"{u.name} ({u.role_name})") for u in users]
    if current_user.role_name == 'Sales Executive':
        form.assigned_to_id.data = current_user.id

    if form.validate_on_submit():
        code = f"LEAD-{uuid.uuid4().hex[:6].upper()}"
        lead = Lead(
            lead_code=code,
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
            company_name=form.company_name.data.strip() if form.company_name.data else None,
            source=form.source.data,
            status=form.status.data,
            priority=form.priority.data,
            expected_value=form.expected_value.data or 0.0,
            notes=form.notes.data.strip() if form.notes.data else None,
            assigned_to_id=form.assigned_to_id.data
        )
        db.session.add(lead)
        db.session.commit()

        log_audit(action='Create', entity_name='Lead', record_id=lead.id, new_value=lead.name)
        flash(f'Lead "{lead.name}" created successfully.', 'success')
        return redirect(url_for('crm.leads_list'))

    return render_template('crm/leads/form.html', form=form, title="Create Lead")

@crm_bp.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def lead_edit(id):
    lead = Lead.query.get_or_404(id)
    if current_user.role_name == 'Sales Executive' and lead.assigned_to_id != current_user.id:
        flash('Access denied: You can only edit your assigned leads.', 'danger')
        return redirect(url_for('crm.leads_list'))

    form = LeadForm(obj=lead)
    users = User.query.filter_by(is_active=True).all()
    form.assigned_to_id.choices = [(u.id, f"{u.name} ({u.role_name})") for u in users]

    if form.validate_on_submit():
        old_val = lead.name
        lead.name = form.name.data.strip()
        lead.email = form.email.data.lower().strip()
        lead.phone = form.phone.data.strip()
        lead.company_name = form.company_name.data.strip() if form.company_name.data else None
        lead.source = form.source.data
        lead.status = form.status.data
        lead.priority = form.priority.data
        lead.expected_value = form.expected_value.data or 0.0
        lead.notes = form.notes.data.strip() if form.notes.data else None
        lead.assigned_to_id = form.assigned_to_id.data

        db.session.commit()
        log_audit(action='Update', entity_name='Lead', record_id=lead.id, old_value=old_val, new_value=lead.name)
        flash(f'Lead "{lead.name}" updated successfully.', 'success')
        return redirect(url_for('crm.leads_list'))

    return render_template('crm/leads/form.html', form=form, title="Edit Lead", lead=lead)

@crm_bp.route('/leads/<int:id>/delete', methods=['POST'])
@login_required
def lead_delete(id):
    lead = Lead.query.get_or_404(id)
    if current_user.role_name not in ['Admin', 'Manager']:
        flash('Access denied: Only Admins and Managers can delete leads.', 'danger')
        return redirect(url_for('crm.leads_list'))

    name = lead.name
    db.session.delete(lead)
    db.session.commit()
    log_audit(action='Delete', entity_name='Lead', record_id=id, old_value=name)
    flash(f'Lead "{name}" deleted.', 'info')
    return redirect(url_for('crm.leads_list'))

@crm_bp.route('/leads/<int:id>/convert', methods=['POST'])
@login_required
def lead_convert(id):
    lead = Lead.query.get_or_404(id)
    if lead.status == 'Converted':
        flash('Lead is already converted.', 'info')
        return redirect(url_for('crm.leads_list'))

    existing_cust = Customer.query.filter_by(email=lead.email).first()
    if existing_cust:
        customer = existing_cust
    else:
        cust_code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
        customer = Customer(
            customer_code=cust_code,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company_name=lead.company_name,
            status='Active',
            owner_id=lead.assigned_to_id,
            created_by_id=current_user.id
        )
        db.session.add(customer)
        db.session.flush()

    opp = None
    if lead.expected_value and lead.expected_value > 0:
        opp = Opportunity(
            name=f"{lead.name} - Converted Opportunity",
            customer_id=customer.id,
            lead_id=lead.id,
            stage='Qualification',
            amount=lead.expected_value,
            probability=50.0,
            expected_close_date=date.today(),
            status='Open',
            owner_id=lead.assigned_to_id
        )
        db.session.add(opp)

    lead.status = 'Converted'
    lead.converted_customer_id = customer.id
    db.session.commit()

    log_audit(action='Lead Conversion', entity_name='Lead', record_id=lead.id, new_value=f"Converted to Customer {customer.id}")
    flash(f'Lead "{lead.name}" successfully converted to Customer and Opportunity!', 'success')
    return redirect(url_for('crm.leads_list'))

# ==========================================
# 3. OPPORTUNITY MANAGEMENT (Create, Edit, Details, Delete, Sales Pipeline)
# ==========================================

@crm_bp.route('/opportunities')
@login_required
def opportunities_list():
    query = get_scoped_query(Opportunity, 'owner_id')
    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    return render_template('crm/opportunities/list.html', opportunities=opportunities)

@crm_bp.route('/opportunities/<int:id>')
@login_required
def opportunity_details(id):
    opp = Opportunity.query.get_or_404(id)
    if current_user.role_name == 'Sales Executive' and opp.owner_id != current_user.id:
        flash('Access denied: You can only view details of your assigned opportunities.', 'danger')
        return redirect(url_for('crm.opportunities_list'))
    return render_template('crm/opportunities/details.html', opportunity=opp)

@crm_bp.route('/opportunities/new', methods=['GET', 'POST'])
@login_required
def opportunity_create():
    form = OpportunityForm()
    customers = Customer.query.filter_by(status='Active').all()
    leads = Lead.query.all()
    users = User.query.filter_by(is_active=True).all()

    form.customer_id.choices = [(0, '-- None --')] + [(c.id, f"{c.name} ({c.company_name or 'N/A'})") for c in customers]
    form.lead_id.choices = [(0, '-- None --')] + [(l.id, l.name) for l in leads]
    form.owner_id.choices = [(u.id, u.name) for u in users]
    if current_user.role_name == 'Sales Executive':
        form.owner_id.data = current_user.id

    if form.validate_on_submit():
        opp = Opportunity(
            name=form.name.data.strip(),
            customer_id=form.customer_id.data if form.customer_id.data != 0 else None,
            lead_id=form.lead_id.data if form.lead_id.data != 0 else None,
            stage=form.stage.data,
            amount=form.amount.data,
            probability=form.probability.data,
            expected_close_date=form.expected_close_date.data,
            status='Won' if form.stage.data == 'Won' else ('Lost' if form.stage.data == 'Lost' else 'Open'),
            notes=form.notes.data.strip() if form.notes.data else None,
            owner_id=form.owner_id.data
        )
        db.session.add(opp)
        db.session.commit()

        log_audit(action='Create', entity_name='Opportunity', record_id=opp.id, new_value=opp.name)
        flash(f'Opportunity "{opp.name}" created successfully.', 'success')
        return redirect(url_for('crm.opportunities_list'))

    return render_template('crm/opportunities/form.html', form=form, title="Create Opportunity")

@crm_bp.route('/opportunities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def opportunity_edit(id):
    opp = Opportunity.query.get_or_404(id)
    if current_user.role_name == 'Sales Executive' and opp.owner_id != current_user.id:
        flash('Access denied: You can only edit your assigned opportunities.', 'danger')
        return redirect(url_for('crm.opportunities_list'))

    form = OpportunityForm(obj=opp)
    customers = Customer.query.filter_by(status='Active').all()
    leads = Lead.query.all()
    users = User.query.filter_by(is_active=True).all()

    form.customer_id.choices = [(0, '-- None --')] + [(c.id, f"{c.name} ({c.company_name or 'N/A'})") for c in customers]
    form.lead_id.choices = [(0, '-- None --')] + [(l.id, l.name) for l in leads]
    form.owner_id.choices = [(u.id, u.name) for u in users]

    if form.validate_on_submit():
        old_val = opp.name
        opp.name = form.name.data.strip()
        opp.customer_id = form.customer_id.data if form.customer_id.data != 0 else None
        opp.lead_id = form.lead_id.data if form.lead_id.data != 0 else None
        opp.stage = form.stage.data
        opp.amount = form.amount.data
        opp.probability = form.probability.data
        opp.expected_close_date = form.expected_close_date.data
        opp.status = 'Won' if form.stage.data == 'Won' else ('Lost' if form.stage.data == 'Lost' else 'Open')
        opp.notes = form.notes.data.strip() if form.notes.data else None
        opp.owner_id = form.owner_id.data

        db.session.commit()
        log_audit(action='Update', entity_name='Opportunity', record_id=opp.id, old_value=old_val, new_value=opp.name)
        flash(f'Opportunity "{opp.name}" updated successfully.', 'success')
        return redirect(url_for('crm.opportunities_list'))

    return render_template('crm/opportunities/form.html', form=form, title="Edit Opportunity", opportunity=opp)

@crm_bp.route('/opportunities/<int:id>/delete', methods=['POST'])
@login_required
def opportunity_delete(id):
    opp = Opportunity.query.get_or_404(id)
    if current_user.role_name not in ['Admin', 'Manager']:
        flash('Access denied: Only Admins and Managers can delete opportunities.', 'danger')
        return redirect(url_for('crm.opportunities_list'))

    name = opp.name
    db.session.delete(opp)
    db.session.commit()
    log_audit(action='Delete', entity_name='Opportunity', record_id=id, old_value=name)
    flash(f'Opportunity "{name}" deleted.', 'info')
    return redirect(url_for('crm.opportunities_list'))

# ==========================================
# 4. FOLLOW-UP (Schedule Follow-Up, Complete Follow-Up, Pending Follow-Ups)
# ==========================================

@crm_bp.route('/followups')
@login_required
def followups_list():
    status_filter = request.args.get('status', '').strip()
    query = get_scoped_query(FollowUp, 'assigned_to_id')

    if status_filter:
        query = query.filter(FollowUp.status == status_filter)

    followups = query.order_by(FollowUp.followup_date.asc()).all()
    return render_template('crm/followups/list.html', followups=followups, status_filter=status_filter)

@crm_bp.route('/followups/new', methods=['GET', 'POST'])
@login_required
def followup_create():
    form = FollowUpForm()
    customers = Customer.query.filter_by(status='Active').all()
    leads = Lead.query.all()
    users = User.query.filter_by(is_active=True).all()

    form.customer_id.choices = [(0, '-- None --')] + [(c.id, c.name) for c in customers]
    form.lead_id.choices = [(0, '-- None --')] + [(l.id, l.name) for l in leads]
    form.assigned_to_id.choices = [(u.id, u.name) for u in users]
    if current_user.role_name == 'Sales Executive':
        form.assigned_to_id.data = current_user.id

    if form.validate_on_submit():
        followup = FollowUp(
            customer_id=form.customer_id.data if form.customer_id.data != 0 else None,
            lead_id=form.lead_id.data if form.lead_id.data != 0 else None,
            followup_date=form.followup_date.data,
            followup_type=form.followup_type.data,
            subject=form.subject.data.strip(),
            remarks=form.remarks.data.strip() if form.remarks.data else None,
            status=form.status.data,
            assigned_to_id=form.assigned_to_id.data
        )
        db.session.add(followup)
        db.session.commit()

        log_audit(action='Create', entity_name='FollowUp', record_id=followup.id, new_value=followup.subject)
        flash(f'Follow-up "{followup.subject}" scheduled successfully.', 'success')
        return redirect(url_for('crm.followups_list'))

    return render_template('crm/followups/form.html', form=form, title="Schedule Follow-Up")

@crm_bp.route('/followups/<int:id>/complete', methods=['POST'])
@login_required
def followup_complete(id):
    followup = FollowUp.query.get_or_404(id)
    followup.status = 'Completed'
    db.session.commit()
    log_audit(action='Update', entity_name='FollowUp', record_id=id, old_value='Planned', new_value='Completed')
    flash('Follow-up marked as Completed!', 'success')
    return redirect(url_for('crm.followups_list'))

# ==========================================
# 5. ACTIVITY MANAGEMENT (Call, Meeting, Email, Task)
# ==========================================

@crm_bp.route('/activities')
@login_required
def activities_list():
    activity_type = request.args.get('type', '').strip()
    query = get_scoped_query(Activity, 'assigned_to_id')

    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)

    activities = query.order_by(Activity.activity_date.desc()).all()
    return render_template('crm/activities/list.html', activities=activities, activity_type=activity_type)

@crm_bp.route('/activities/new', methods=['GET', 'POST'])
@login_required
def activity_create():
    if request.method == 'POST':
        act_type = request.form.get('activity_type', 'Call')
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        customer_id = request.form.get('customer_id', type=int)
        lead_id = request.form.get('lead_id', type=int)

        if not subject:
            flash('Activity subject is required.', 'danger')
            return redirect(url_for('crm.activities_list'))

        activity = Activity(
            activity_type=act_type,
            subject=subject,
            description=description if description else None,
            activity_date=datetime.now(),
            customer_id=customer_id if customer_id != 0 else None,
            lead_id=lead_id if lead_id != 0 else None,
            assigned_to_id=current_user.id,
            status='Completed'
        )
        db.session.add(activity)
        db.session.commit()

        log_audit(action='Create Activity', entity_name='Activity', record_id=activity.id, new_value=f"{act_type}: {subject}")
        flash(f'Activity ({act_type}) logged successfully!', 'success')
        return redirect(url_for('crm.activities_list'))

    customers = Customer.query.filter_by(status='Active').all()
    leads = Lead.query.all()
    return render_template('crm/activities/form.html', customers=customers, leads=leads)
