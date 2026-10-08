from datetime import date, datetime
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, FloatField, IntegerField, TextAreaField, DateField, DateTimeLocalField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError, Optional
from app.models import User, Customer, Lead

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    role_id = SelectField('Role', coerce=int, validators=[
        DataRequired(message="Select a role.")
    ])
    submit = SubmitField('Register User')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('Email address is already registered.')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[
        DataRequired(message="Customer Name is required."),
        Length(min=2, max=100, message="Customer Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required.")
    ])
    company_name = StringField('Company Name', validators=[Optional(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=50)])
    state = StringField('State', validators=[Optional(), Length(max=50)])
    status = SelectField('Status', choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    owner_id = SelectField('Assigned Owner', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Customer')

    def __init__(self, original_customer=None, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.original_customer = original_customer

    def validate_phone(self, field):
        cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', field.data)
        if not cleaned_phone.isdigit() or len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
            raise ValidationError('Enter a valid phone number (10 to 15 digits).')
        
        # Uniqueness check
        existing = Customer.query.filter_by(phone=field.data.strip()).first()
        if existing and (not self.original_customer or existing.id != self.original_customer.id):
            raise ValidationError('Customer with this phone number already exists.')

    def validate_email(self, field):
        existing = Customer.query.filter_by(email=field.data.lower().strip()).first()
        if existing and (not self.original_customer or existing.id != self.original_customer.id):
            raise ValidationError('Customer with this email address already exists.')

class LeadForm(FlaskForm):
    name = StringField('Lead Name', validators=[
        DataRequired(message="Lead Name is required."),
        Length(min=2, max=100, message="Lead Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required.")
    ])
    company_name = StringField('Company Name', validators=[Optional(), Length(max=100)])
    source = SelectField('Lead Source', choices=[
        ('Website', 'Website'),
        ('Referral', 'Referral'),
        ('Social Media', 'Social Media'),
        ('Cold Call', 'Cold Call'),
        ('Event', 'Event'),
        ('Other', 'Other')
    ], default='Website')
    status = SelectField('Status', choices=[
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Qualified', 'Qualified'),
        ('Unqualified', 'Unqualified'),
        ('Converted', 'Converted'),
        ('Lost', 'Lost')
    ], default='New')
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], default='Medium')
    expected_value = FloatField('Expected Value ($)', validators=[
        Optional(),
        NumberRange(min=0, message="Expected value cannot be negative.")
    ], default=0.0)
    notes = TextAreaField('Notes', validators=[Optional()])
    assigned_to_id = SelectField('Assigned To', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Lead')

    def validate_phone(self, field):
        cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', field.data)
        if not cleaned_phone.isdigit() or len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
            raise ValidationError('Enter a valid phone number.')

class OpportunityForm(FlaskForm):
    name = StringField('Opportunity Name', validators=[
        DataRequired(message="Opportunity Name is required."),
        Length(min=2, max=100, message="Opportunity Name must be between 2 and 100 characters.")
    ])
    customer_id = SelectField('Customer', coerce=int, validators=[Optional()])
    lead_id = SelectField('Related Lead', coerce=int, validators=[Optional()])
    stage = SelectField('Pipeline Stage', choices=[
        ('Qualification', 'Qualification'),
        ('Proposal', 'Proposal'),
        ('Negotiation', 'Negotiation'),
        ('Won', 'Won'),
        ('Lost', 'Lost')
    ], default='Qualification')
    amount = FloatField('Amount ($)', validators=[
        DataRequired(message="Opportunity Amount is required."),
        NumberRange(min=0.01, message="Opportunity Amount must be greater than 0.")
    ])
    probability = FloatField('Probability (%)', validators=[
        DataRequired(message="Probability is required."),
        NumberRange(min=0, max=100, message="Probability must be between 0 and 100.")
    ], default=50.0)
    expected_close_date = DateField('Expected Close Date', format='%Y-%m-%d', validators=[
        DataRequired(message="Expected Close Date is required.")
    ])
    notes = TextAreaField('Notes', validators=[Optional()])
    owner_id = SelectField('Owner', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Opportunity')

    def validate_expected_close_date(self, field):
        if field.data and field.data < date.today() and self.stage.data not in ['Won', 'Lost']:
            raise ValidationError('Expected Close Date cannot be in the past for an active Opportunity.')

class FollowUpForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[Optional()])
    lead_id = SelectField('Related Lead', coerce=int, validators=[Optional()])
    followup_date = DateTimeLocalField('Follow-Up Date & Time', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message="Follow-Up Date & Time is required.")
    ])
    followup_type = SelectField('Activity Type', choices=[
        ('Call', 'Call'),
        ('Meeting', 'Meeting'),
        ('Email', 'Email'),
        ('Task', 'Task')
    ], default='Call')
    subject = StringField('Subject', validators=[
        DataRequired(message="Subject is required."),
        Length(max=200)
    ])
    remarks = TextAreaField('Remarks / Notes', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Planned', 'Planned'),
        ('Completed', 'Completed'),
        ('Missed', 'Missed'),
        ('Cancelled', 'Cancelled')
    ], default='Planned')
    assigned_to_id = SelectField('Assigned To', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Schedule Follow-Up')

    def validate_followup_date(self, field):
        if field.data and field.data < datetime.now() and self.status.data == 'Planned':
            raise ValidationError('Follow-up date cannot be earlier than today for a new/planned follow-up.')

class UserEditForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Account Active')
    submit = SubmitField('Update User')
