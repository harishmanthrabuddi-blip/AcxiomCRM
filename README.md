# AcxiomCRM — Enterprise Customer Relationship Management System

> **A production-oriented, role-based CRM application built with Python, Flask, SQLite, Bootstrap 5, and Chart.js.**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

---

## 📌 Executive Overview

**AcxiomCRM** is a full-featured web-based CRM solution covering the complete customer-sales lifecycle — from initial prospect lead capture and qualification to customer management, opportunity pipeline forecasting, follow-up scheduling, activity tracking, audit logging, and reporting.

The system enforces multi-level client & server-side validation, role-based authorization (RBAC), security controls (password policies, account lockout, anti-forgery CSRF protection), and RESTful JSON APIs.

---

## 🚀 Key Features & Functional Modules

### 🔐 1. Authentication & Security Baseline
- **Role-Based Access Control (RBAC)**: Supports `Admin`, `Manager`, and `Sales Executive` access scopes.
- **Account Lockout Policy**: Automatically locks user accounts for 15 minutes after 5 consecutive failed login attempts.
- **Password Protection**: Secure password hashing using Werkzeug adaptive security methods.
- **Anti-Forgery Protection**: State-changing POST forms protected via `Flask-WTF` CSRF tokens.

### 📊 2. Executive Dashboard & Analytics
- **Role-Scoped KPIs**: Total Customers, Open Leads, Open Opportunities, and Total Pipeline Value ($).
- **Chart.js Visualizations**:
  - *Lead Status Breakdown* (Doughnut Chart: New, Contacted, Qualified, Converted, Lost)
  - *Opportunity Pipeline Value* (Bar Chart: Qualification, Proposal, Negotiation, Won, Lost)
- **Planned Follow-Ups Table**: Quick-action view for upcoming sales tasks with instant completion.

### 👥 3. Customer Management
- Master customer directory with search by name, email, phone, or company.
- Uniqueness validation on email and 10-15 digit phone numbers.
- Owner assignment and customer history tracking.

### 🎯 4. Lead Management & Conversion Workflow
- Capture prospect leads by source (`Website`, `Referral`, `Social Media`, `Cold Call`, `Event`, `Other`).
- **One-Click Lead Conversion**: Automatically converts qualified leads into active Customer and Opportunity records while creating audit log entries.

### 📈 5. Opportunity Management & Weighted Pipeline
- Deal stage tracking (`Qualification`, `Proposal`, `Negotiation`, `Won`, `Lost`).
- **Weighted Revenue Forecasting**: Automatically derives deal value (`Amount × Probability / 100`).
- Strict Business Validation: Amount > 0, Probability between 0–100%, Expected Close Date >= today.

### 📅 6. Follow-Up & Activity Management
- Schedule and track follow-ups (`Call`, `Meeting`, `Email`, `Task`).
- Date validation: Planned follow-up dates cannot be earlier than today.

### ⚙️ 7. User Administration & Audit Log
- **User Management**: Admins can edit users, assign roles, activate/deactivate accounts, and unlock locked accounts.
- **Centralized Audit Logging**: Append-only audit trail capturing user, timestamp, action, entity, record ID, old/new values, and client IP address.

### 🔌 8. Secured REST APIs
- Secured JSON endpoints (`/api/auth/login`, `/api/customers`, `/api/leads`, `/api/opportunities`, `/api/reports/pipeline`) using DTO response objects.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Language** | Python 3.10+ |
| **Web Framework** | Flask 3.x |
| **ORM & Database** | Flask-SQLAlchemy 3.x + SQLite |
| **Database Migrations**| Flask-Migrate (Alembic) |
| **Authentication** | Flask-Login |
| **Password Security** | Werkzeug Security |
| **Forms & CSRF** | Flask-WTF + WTForms |
| **Environment Config** | python-dotenv |
| **UI Framework** | HTML5, CSS3, Bootstrap 5 |
| **Data Visualization** | Chart.js 4.4 |
| **Automated Testing** | pytest |

---

## 📁 Repository Structure

```
AcxiomCRM/
├── .env                  # Environment variables
├── .gitignore            # Git ignore rules
├── config.py             # Application configuration
├── requirements.txt      # Python dependencies
├── run.py                # Main application entry point
├── seed_db.py            # Database initialization and seeding script
├── verify_server.py      # Automated HTTP server endpoint test
├── instance/             # SQLite database storage (acxiomcrm.db)
├── app/                  # Core Application Package
│   ├── __init__.py       # App factory (create_app)
│   ├── extensions.py     # Database & Login extension objects
│   ├── models.py         # SQLAlchemy Data Models
│   ├── forms.py          # WTForms definitions & custom validators
│   ├── routes.py         # Main dashboard routes & KPI calculations
│   ├── admin/            # User administration & Audit log blueprint
│   ├── api/              # REST API blueprint endpoints
│   ├── auth/             # Login, logout & registration blueprint
│   ├── crm/              # Customers, Leads, Opportunities & FollowUps blueprint
│   ├── reports/          # Tabular reports & export blueprint
│   ├── services/         # Centralized audit logger service
│   ├── static/           # CSS and static assets
│   └── templates/        # Jinja2 HTML templates
└── tests/                # Automated Pytest Suite
    ├── test_auth.py
    └── test_crm_and_api.py
```

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/harishmanthrabuddi-blip/AcxiomCRM.git
cd AcxiomCRM
```

### 2. Set Up Virtual Environment
```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize & Seed Database
```bash
python seed_db.py
```

### 5. Run the Application
```bash
python run.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🔑 Default Login Credentials

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@acxiom.com` | `Admin@123` | Full system administration, user roles, audit logs, all CRM data & reports |
| **Manager** | `manager@acxiom.com` | `Manager@123` | Team pipeline monitoring, customer/lead CRUD, team reports |
| **Sales Executive**| `sales@acxiom.com` | `Sales@123` | Own/assigned customers, leads, opportunities, follow-ups & sales dashboard |

---

## 🧪 Running Automated Tests

Run the full `pytest` test suite:

```bash
pytest
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
