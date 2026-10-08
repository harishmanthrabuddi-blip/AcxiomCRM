from datetime import datetime, date, timedelta
from app import create_app
from app.extensions import db
from app.models import Role, User, Customer, Lead, Opportunity, FollowUp, AuditLog

app = create_app()

def seed_database():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Seed Roles
        roles_data = [
            ('Admin', 'Full application administration, user/role management, audit logs, and all CRM records.'),
            ('Manager', 'Team/customer/lead/opportunity management and team reports.'),
            ('Sales Executive', 'Assigned customers, leads, opportunities, follow-ups, and sales dashboard.')
        ]

        roles_dict = {}
        for role_name, description in roles_data:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=description)
                db.session.add(role)
            roles_dict[role_name] = role

        db.session.commit()

        # Reload roles
        for r in Role.query.all():
            roles_dict[r.name] = r

        # Seed Users
        users_seed = [
            ('System Administrator', 'admin@acxiom.com', 'Admin@123', 'Admin'),
            ('Sales Manager', 'manager@acxiom.com', 'Manager@123', 'Manager'),
            ('Sales Executive', 'sales@acxiom.com', 'Sales@123', 'Sales Executive')
        ]

        users_dict = {}
        for name, email, password, role_name in users_seed:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    name=name,
                    email=email,
                    role_id=roles_dict[role_name].id,
                    is_active=True
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                print(f"Created User: {email}")
            users_dict[role_name] = user

        admin_user = users_dict['Admin']
        manager_user = users_dict['Manager']
        sales_user = users_dict['Sales Executive']

        # Seed Customers
        if Customer.query.count() == 0:
            customers_data = [
                ('Acme Enterprises', 'contact@acme.com', '9876543210', 'Acme Corp', '123 Tech Park', 'San Jose', 'CA', sales_user.id),
                ('Globex Corporation', 'info@globex.com', '9876543211', 'Globex Inc', '456 Business Way', 'Chicago', 'IL', sales_user.id),
                ('Stark Industries', 'sales@stark.com', '9876543212', 'Stark Ind', '10880 Wilshire Blvd', 'Los Angeles', 'CA', manager_user.id)
            ]
            for i, (name, email, phone, comp, addr, city, state, owner_id) in enumerate(customers_data, 1):
                c = Customer(
                    customer_code=f"CUST-00{i}",
                    name=name,
                    email=email,
                    phone=phone,
                    company_name=comp,
                    address=addr,
                    city=city,
                    state=state,
                    status='Active',
                    owner_id=owner_id,
                    created_by_id=admin_user.id
                )
                db.session.add(c)
            db.session.commit()
            print("Seeded Customers.")

        # Seed Leads
        if Lead.query.count() == 0:
            leads_data = [
                ('Wayne Enterprises', 'bruce@wayne.com', '9123456780', 'Wayne Enterprises', 'Website', 'New', 'High', 150000.0, sales_user.id),
                ('Cyberdyne Systems', 'miles@cyberdyne.com', '9123456781', 'Cyberdyne', 'Referral', 'Contacted', 'Medium', 85000.0, sales_user.id),
                ('Umbrella Corp', 'albert@umbrella.com', '9123456782', 'Umbrella Corp', 'Cold Call', 'Qualified', 'High', 220000.0, manager_user.id),
                ('Massive Dynamic', 'nina@massivedynamic.com', '9123456783', 'Massive Dynamic', 'Event', 'Converted', 'Medium', 50000.0, sales_user.id)
            ]
            for i, (name, email, phone, comp, source, status, priority, val, owner_id) in enumerate(leads_data, 1):
                l = Lead(
                    lead_code=f"LEAD-00{i}",
                    name=name,
                    email=email,
                    phone=phone,
                    company_name=comp,
                    source=source,
                    status=status,
                    priority=priority,
                    expected_value=val,
                    assigned_to_id=owner_id
                )
                db.session.add(l)
            db.session.commit()
            print("Seeded Leads.")

        # Seed Opportunities
        if Opportunity.query.count() == 0:
            cust1 = Customer.query.first()
            opps_data = [
                ('Acme Cloud ERP Migration', cust1.id if cust1 else None, 'Proposal', 120000.0, 75.0, date.today() + timedelta(days=30), 'Open', sales_user.id),
                ('Globex CRM Suite Upgrade', cust1.id if cust1 else None, 'Qualification', 65000.0, 40.0, date.today() + timedelta(days=45), 'Open', sales_user.id),
                ('Stark Security System Rollout', cust1.id if cust1 else None, 'Negotiation', 300000.0, 90.0, date.today() + timedelta(days=15), 'Open', manager_user.id),
                ('Soylent Analytics Contract', None, 'Won', 45000.0, 100.0, date.today() - timedelta(days=10), 'Won', sales_user.id)
            ]
            for name, cust_id, stage, amt, prob, close_date, status, owner_id in opps_data:
                o = Opportunity(
                    name=name,
                    customer_id=cust_id,
                    stage=stage,
                    amount=amt,
                    probability=prob,
                    expected_close_date=close_date,
                    status=status,
                    owner_id=owner_id
                )
                db.session.add(o)
            db.session.commit()
            print("Seeded Opportunities.")

        # Seed FollowUps
        if FollowUp.query.count() == 0:
            cust1 = Customer.query.first()
            lead1 = Lead.query.first()
            followups_data = [
                (cust1.id if cust1 else None, None, datetime.now() + timedelta(days=1), 'Call', 'Follow-up on proposal pricing', 'Planned', sales_user.id),
                (None, lead1.id if lead1 else None, datetime.now() + timedelta(days=2), 'Meeting', 'Demonstrate AcxiomCRM features', 'Planned', sales_user.id),
                (cust1.id if cust1 else None, None, datetime.now() - timedelta(days=1), 'Email', 'Sent contract draft', 'Completed', manager_user.id)
            ]
            for c_id, l_id, f_date, f_type, subj, status, owner_id in followups_data:
                f = FollowUp(
                    customer_id=c_id,
                    lead_id=l_id,
                    followup_date=f_date,
                    followup_type=f_type,
                    subject=subj,
                    status=status,
                    assigned_to_id=owner_id
                )
                db.session.add(f)
            db.session.commit()
            print("Seeded FollowUps.")

        # Seed Audit Logs
        if AuditLog.query.count() == 0:
            audit_events = [
                (admin_user.id, 'Login', 'User', admin_user.id, None, 'User authenticated successfully', datetime.now() - timedelta(hours=5)),
                (admin_user.id, 'Create', 'Customer', 1, None, 'Acme Enterprises', datetime.now() - timedelta(hours=4)),
                (sales_user.id, 'Create', 'Lead', 1, None, 'Wayne Enterprises', datetime.now() - timedelta(hours=3)),
                (sales_user.id, 'Lead Conversion', 'Lead', 4, 'Status: Qualified', 'Converted to Customer 4', datetime.now() - timedelta(hours=2)),
                (admin_user.id, 'Role/User Update', 'User', sales_user.id, 'Role: Sales Executive', 'Role: Sales Executive, Active: True', datetime.now() - timedelta(hours=1))
            ]
            for uid, action, entity, rec_id, old_v, new_v, dt in audit_events:
                a = AuditLog(
                    user_id=uid,
                    action=action,
                    entity_name=entity,
                    record_id=rec_id,
                    old_value=old_v,
                    new_value=new_v,
                    created_at=dt,
                    ip_address='127.0.0.1'
                )
                db.session.add(a)
            db.session.commit()
            print("Seeded Audit Logs.")

        print("All database tables and seed data created successfully.")

if __name__ == '__main__':
    seed_database()
