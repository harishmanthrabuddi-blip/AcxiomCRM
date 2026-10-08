import pytest
from app import create_app
from app.extensions import db
from app.models import User, Role

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
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator')
            manager_role = Role(name='Manager', description='Manager')
            sales_role = Role(name='Sales Executive', description='Sales Exec')
            db.session.add_all([admin_role, manager_role, sales_role])
            db.session.commit()

        user = User.query.filter_by(email='testadmin@acxiom.com').first()
        if not user:
            user = User(name='Test Admin', email='testadmin@acxiom.com', role_id=admin_role.id)
            user.set_password('Secret123!')
            db.session.add(user)
            db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_password_hashing(app):
    with app.app_context():
        user = User.query.filter_by(email='testadmin@acxiom.com').first()
        assert user.check_password('Secret123!') is True
        assert user.check_password('WrongPassword') is False
        assert user.password_hash != 'Secret123!'

def test_login_success(client):
    response = client.post('/auth/login', data={
        'email': 'testadmin@acxiom.com',
        'password': 'Secret123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back, Test Admin!' in response.data

def test_login_failure_count_and_lockout(client, app):
    # Perform 5 failed login attempts
    for i in range(5):
        client.post('/auth/login', data={
            'email': 'testadmin@acxiom.com',
            'password': 'WrongPassword'
        })

    with app.app_context():
        user = User.query.filter_by(email='testadmin@acxiom.com').first()
        assert user.failed_login_count == 5
        assert user.is_locked_out() is True

    # Try logging in with correct password while locked out -> should be rejected
    response = client.post('/auth/login', data={
        'email': 'testadmin@acxiom.com',
        'password': 'Secret123!'
    }, follow_redirects=True)

    assert b'Account is temporarily locked' in response.data or b'locked for 15 minutes' in response.data

def test_logout(client):
    client.post('/auth/login', data={
        'email': 'testadmin@acxiom.com',
        'password': 'Secret123!'
    })
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out successfully.' in response.data
