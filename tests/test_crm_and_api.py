import pytest
from datetime import date, datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Role, Customer, Lead, Opportunity, FollowUp

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        db.create_all()
        admin_role = Role(name='Admin', description='Admin')
        sales_role = Role(name='Sales Executive', description='Sales Exec')
        db.session.add_all([admin_role, sales_role])
        db.session.commit()

        admin = User(name='Admin User', email='admin@test.com', role_id=admin_role.id)
        admin.set_password('Admin123!')

        sales = User(name='Sales User', email='sales@test.com', role_id=sales_role.id)
        sales.set_password('Sales123!')

        db.session.add_all([admin, sales])
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def login_client(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

def test_customer_creation_and_uniqueness(client, app):
    login_client(client, 'admin@test.com', 'Admin123!')

    with app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        res = client.post('/crm/customers/new', data={
            'name': 'Test Corp',
            'email': 'corp@test.com',
            'phone': '9876543210',
            'status': 'Active',
            'owner_id': admin.id
        }, follow_redirects=True)
        assert res.status_code == 200
        assert Customer.query.filter_by(email='corp@test.com').first() is not None

        # Duplicate email test
        res_dup = client.post('/crm/customers/new', data={
            'name': 'Duplicate Corp',
            'email': 'corp@test.com',
            'phone': '9998887770',
            'status': 'Active',
            'owner_id': admin.id
        }, follow_redirects=True)
        assert b'Customer with this email address already exists.' in res_dup.data

def test_lead_conversion_workflow(client, app):
    login_client(client, 'admin@test.com', 'Admin123!')

    with app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        lead = Lead(
            lead_code='LEAD-101',
            name='Convertible Lead',
            email='convert@test.com',
            phone='9112233445',
            status='Qualified',
            expected_value=50000.0,
            assigned_to_id=admin.id
        )
        db.session.add(lead)
        db.session.commit()
        lead_id = lead.id

    res = client.post(f'/crm/leads/{lead_id}/convert', follow_redirects=True)
    assert res.status_code == 200
    assert b'converted to Customer and Opportunity' in res.data

    with app.app_context():
        converted_lead = db.session.get(Lead, lead_id)
        assert converted_lead.status == 'Converted'
        assert converted_lead.converted_customer_id is not None
        assert Opportunity.query.filter_by(customer_id=converted_lead.converted_customer_id).first() is not None

def test_rest_api_endpoints(client, app):
    # Test API login
    login_res = client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'Admin123!'
    })
    assert login_res.status_code == 200
    assert login_res.json['user']['email'] == 'admin@test.com'

    # Test GET customers API
    cust_res = client.get('/api/customers')
    assert cust_res.status_code == 200
    assert isinstance(cust_res.json, list)

    # Test GET pipeline report API
    pipe_res = client.get('/api/reports/pipeline')
    assert pipe_res.status_code == 200
    assert 'pipeline_summary' in pipe_res.json
