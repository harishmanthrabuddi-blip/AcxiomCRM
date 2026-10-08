from flask import request
from flask_login import current_user
from app.extensions import db
from app.models import AuditLog

def log_audit(action, entity_name, record_id=None, old_value=None, new_value=None):
    try:
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        ip_addr = request.remote_addr if request else None

        audit = AuditLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            record_id=record_id,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            ip_address=ip_addr
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit: {e}")
