from app import create_app
from app.models import AuditLog

app = create_app()

with app.app_context():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    print("=" * 80)
    print(f"ACXIOMCRM AUDIT LOG CHECK -- Total Log Entries: {len(logs)}")
    print("=" * 80)

    for l in logs:
        user_name = l.user.name if l.user else "System / Anonymous"
        print(f"ID #{l.id:04d} | {l.created_at.strftime('%Y-%m-%d %H:%M:%S')} | User: {user_name:<20} | Action: {l.action:<18} | Entity: {l.entity_name:<10} #{l.record_id or 0}")
        if l.old_value or l.new_value:
            print(f"         +-- Old: {l.old_value}  -->  New: {l.new_value}")
        print("-" * 80)
