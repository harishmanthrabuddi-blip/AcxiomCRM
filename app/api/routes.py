from datetime import datetime, date
import uuid
from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from app.api import api_bp
from app.extensions import db, csrf
from app.models import Customer, Lead, Opportunity, User, Role
from app.services.audit import log_audit

# Exempt API endpoints from CSRF for programmatic API usage (tokens/HTTP authentication)
csrf.exempt(api_bp)

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials.'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated.'}), 403

    if user.is_locked_out():
        return jsonify({'error': 'Account is locked.'}), 403

    user.reset_failed_login()
    login_user(user)
    log_audit(action='API Login', entity_name='User', record_id=user.id)
    return jsonify({
        'message': 'Login successful.',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role_name
        }
    }), 200

@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully.'}), 200

@api_bp.route('/customers', methods=['GET'])
@login_required
def api_get_customers():
    query = Customer.query
    if current_user.role_name == 'Sales Executive':
        query = query.filter_by(owner_id=current_user.id)

    customers = query.all()
    return jsonify([c.to_dict() for c in customers]), 200

@api_bp.route('/customers/<int:id>', methods=['GET'])
@login_required
def api_get_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({'error': 'Customer not found.'}), 404

    if current_user.role_name == 'Sales Executive' and customer.owner_id != current_user.id:
        return jsonify({'error': 'Access denied.'}), 403

    return jsonify(customer.to_dict()), 200

@api_bp.route('/customers', methods=['POST'])
@login_required
def api_create_customer():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()

    if not name or not email or not phone:
        return jsonify({'error': 'Name, email, and phone are required.'}), 400

    if Customer.query.filter_by(email=email).first():
        return jsonify({'error': 'Customer with this email already exists.'}), 409

    if Customer.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Customer with this phone already exists.'}), 409

    code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
    customer = Customer(
        customer_code=code,
        name=name,
        email=email,
        phone=phone,
        company_name=data.get('company_name'),
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        status=data.get('status', 'Active'),
        owner_id=data.get('owner_id', current_user.id),
        created_by_id=current_user.id
    )
    db.session.add(customer)
    db.session.commit()

    log_audit(action='API Create', entity_name='Customer', record_id=customer.id, new_value=customer.name)
    return jsonify(customer.to_dict()), 201

@api_bp.route('/customers/<int:id>', methods=['PUT'])
@login_required
def api_update_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({'error': 'Customer not found.'}), 404

    if current_user.role_name == 'Sales Executive' and customer.owner_id != current_user.id:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json() or {}
    if 'name' in data:
        customer.name = data['name'].strip()
    if 'company_name' in data:
        customer.company_name = data['company_name']
    if 'status' in data:
        customer.status = data['status']

    db.session.commit()
    log_audit(action='API Update', entity_name='Customer', record_id=customer.id, new_value=customer.name)
    return jsonify(customer.to_dict()), 200

@api_bp.route('/customers/<int:id>', methods=['DELETE'])
@login_required
def api_delete_customer(id):
    if current_user.role_name not in ['Admin', 'Manager']:
        return jsonify({'error': 'Access denied. Administrator or Manager required.'}), 403

    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({'error': 'Customer not found.'}), 404

    db.session.delete(customer)
    db.session.commit()
    log_audit(action='API Delete', entity_name='Customer', record_id=id)
    return jsonify({'message': 'Customer deleted successfully.'}), 200

@api_bp.route('/leads', methods=['GET'])
@login_required
def api_get_leads():
    query = Lead.query
    if current_user.role_name == 'Sales Executive':
        query = query.filter_by(assigned_to_id=current_user.id)

    leads = query.all()
    return jsonify([l.to_dict() for l in leads]), 200

@api_bp.route('/leads', methods=['POST'])
@login_required
def api_create_lead():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()

    if not name or not email or not phone:
        return jsonify({'error': 'Name, email, and phone are required.'}), 400

    code = f"LEAD-{uuid.uuid4().hex[:6].upper()}"
    lead = Lead(
        lead_code=code,
        name=name,
        email=email,
        phone=phone,
        company_name=data.get('company_name'),
        source=data.get('source', 'Website'),
        status=data.get('status', 'New'),
        priority=data.get('priority', 'Medium'),
        expected_value=float(data.get('expected_value', 0.0)),
        assigned_to_id=data.get('assigned_to_id', current_user.id)
    )
    db.session.add(lead)
    db.session.commit()

    log_audit(action='API Create', entity_name='Lead', record_id=lead.id, new_value=lead.name)
    return jsonify(lead.to_dict()), 201

@api_bp.route('/opportunities', methods=['GET'])
@login_required
def api_get_opportunities():
    query = Opportunity.query
    if current_user.role_name == 'Sales Executive':
        query = query.filter_by(owner_id=current_user.id)

    opportunities = query.all()
    return jsonify([o.to_dict() for o in opportunities]), 200

@api_bp.route('/reports/pipeline', methods=['GET'])
@login_required
def api_reports_pipeline():
    query = Opportunity.query
    if current_user.role_name == 'Sales Executive':
        query = query.filter_by(owner_id=current_user.id)

    opportunities = query.all()
    stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']
    stage_summary = {stage: {'count': 0, 'total_amount': 0.0, 'weighted_amount': 0.0} for stage in stages}

    for opp in opportunities:
        if opp.stage in stage_summary:
            stage_summary[opp.stage]['count'] += 1
            stage_summary[opp.stage]['total_amount'] += opp.amount
            stage_summary[opp.stage]['weighted_amount'] += opp.weighted_amount

    return jsonify({
        'pipeline_summary': stage_summary,
        'total_opportunities': len(opportunities),
        'total_pipeline_value': sum(o.amount for o in opportunities)
    }), 200
