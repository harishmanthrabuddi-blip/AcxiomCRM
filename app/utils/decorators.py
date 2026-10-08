from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role_name not in roles and 'Admin' not in roles:
                flash('Access denied: You do not have permission to access this resource.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return roles_required('Admin')(f)

def manager_required(f):
    return roles_required('Admin', 'Manager')(f)
