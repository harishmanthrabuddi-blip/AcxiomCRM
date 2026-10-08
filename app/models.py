from datetime import datetime, timedelta, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    lockout_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    owned_customers = db.relationship('Customer', foreign_keys='Customer.owner_id', backref='owner', lazy=True)
    assigned_leads = db.relationship('Lead', foreign_keys='Lead.assigned_to_id', backref='assigned_to', lazy=True)
    owned_opportunities = db.relationship('Opportunity', foreign_keys='Opportunity.owner_id', backref='owner', lazy=True)
    assigned_followups = db.relationship('FollowUp', foreign_keys='FollowUp.assigned_to_id', backref='assigned_to', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_locked_out(self):
        if self.lockout_until and datetime.utcnow() < self.lockout_until:
            return True
        return False

    def record_failed_login(self, max_attempts=5, lockout_minutes=15):
        self.failed_login_count += 1
        if self.failed_login_count >= max_attempts:
            self.lockout_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
        db.session.commit()

    def reset_failed_login(self):
        self.failed_login_count = 0
        self.lockout_until = None
        db.session.commit()

    @property
    def role_name(self):
        return self.role.name if self.role else 'Sales Executive'

    def __repr__(self):
        return f'<User {self.email} - Role: {self.role_name}>'

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Active', nullable=False) # Active, Inactive
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    opportunities = db.relationship('Opportunity', backref='customer', lazy=True)
    followups = db.relationship('FollowUp', backref='customer', lazy=True)
    activities = db.relationship('Activity', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_code': self.customer_code,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company_name': self.company_name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Lead(db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    lead_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(50), default='Website', nullable=False) # Website, Referral, Social Media, Cold Call, Event, Other
    status = db.Column(db.String(30), default='New', nullable=False) # New, Contacted, Qualified, Unqualified, Converted, Lost
    priority = db.Column(db.String(20), default='Medium', nullable=False) # Low, Medium, High
    expected_value = db.Column(db.Float, default=0.0, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    converted_customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    converted_customer = db.relationship('Customer', foreign_keys=[converted_customer_id], backref='source_lead', lazy=True)
    opportunities = db.relationship('Opportunity', backref='lead', lazy=True)
    followups = db.relationship('FollowUp', backref='lead', lazy=True)
    activities = db.relationship('Activity', backref='lead', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'lead_code': self.lead_code,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company_name': self.company_name,
            'source': self.source,
            'status': self.status,
            'priority': self.priority,
            'expected_value': self.expected_value,
            'notes': self.notes,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to.name if self.assigned_to else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Opportunity(db.Model):
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    stage = db.Column(db.String(30), default='Qualification', nullable=False) # Qualification, Proposal, Negotiation, Won, Lost
    amount = db.Column(db.Float, nullable=False)
    probability = db.Column(db.Float, default=50.0, nullable=False) # 0 to 100
    expected_close_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Open', nullable=False) # Open, Won, Lost
    notes = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def weighted_amount(self):
        return self.amount * (self.probability / 100.0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'lead_id': self.lead_id,
            'stage': self.stage,
            'amount': self.amount,
            'probability': self.probability,
            'weighted_amount': round(self.weighted_amount, 2),
            'expected_close_date': self.expected_close_date.strftime('%Y-%m-%d') if self.expected_close_date else None,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class FollowUp(db.Model):
    __tablename__ = 'followups'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    followup_date = db.Column(db.DateTime, nullable=False)
    followup_type = db.Column(db.String(30), default='Call', nullable=False) # Call, Meeting, Email, Task
    subject = db.Column(db.String(200), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Planned', nullable=False) # Planned, Completed, Missed, Cancelled
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'lead_id': self.lead_id,
            'lead_name': self.lead.name if self.lead else None,
            'followup_date': self.followup_date.strftime('%Y-%m-%d %H:%M') if self.followup_date else None,
            'followup_type': self.followup_type,
            'subject': self.subject,
            'remarks': self.remarks,
            'status': self.status,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to.name if self.assigned_to else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(30), nullable=False) # Call, Meeting, Email, Task
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    activity_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='Completed', nullable=False) # Completed, Pending

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entity_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='audit_logs', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'System/Anonymous',
            'action': self.action,
            'entity_name': self.entity_name,
            'record_id': self.record_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'ip_address': self.ip_address
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
