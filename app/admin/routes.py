from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.extensions import db
from app.models import User, Role, AuditLog
from app.forms import UserEditForm
from app.utils.decorators import admin_required, manager_required
from app.services.audit import log_audit

@admin_bp.route('/users')
@login_required
@manager_required
def users_list():
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()

    query = User.query

    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    if role_filter:
        query = query.join(Role).filter(Role.name == role_filter)

    users = query.order_by(User.id.asc()).all()
    roles = Role.query.all()
    return render_template('admin/users/list.html', users=users, roles=roles, search=search, role_filter=role_filter)

@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
    user = User.query.get_or_404(id)
    form = UserEditForm(obj=user)
    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    if form.validate_on_submit():
        old_val = f"Name: {user.name}, Role: {user.role_name}, Active: {user.is_active}"
        user.name = form.name.data.strip()
        user.email = form.email.data.lower().strip()
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data

        db.session.commit()
        new_val = f"Name: {user.name}, Role: {user.role_name}, Active: {user.is_active}"
        log_audit(action='Role/User Update', entity_name='User', record_id=user.id, old_value=old_val, new_value=new_val)
        flash(f'User "{user.name}" updated successfully.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users/form.html', form=form, user=user)

@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def user_toggle_status(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    db.session.commit()
    log_audit(action='Status Change', entity_name='User', record_id=id, new_value=f"is_active={user.is_active}")
    status_str = "activated" if user.is_active else "deactivated"
    flash(f'User "{user.name}" has been {status_str}.', 'info')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/users/<int:id>/unlock', methods=['POST'])
@login_required
@admin_required
def user_unlock(id):
    user = User.query.get_or_404(id)
    user.reset_failed_login()
    log_audit(action='Account Unlock', entity_name='User', record_id=id, new_value='Unlocked by Admin')
    flash(f'Account for "{user.name}" has been unlocked.', 'success')
    return redirect(url_for('admin.users_list'))

@admin_bp.route('/audit-logs')
@login_required
@manager_required
def audit_logs():
    action_filter = request.args.get('action', '').strip()
    entity_filter = request.args.get('entity', '').strip()

    query = AuditLog.query

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if entity_filter:
        query = query.filter(AuditLog.entity_name == entity_filter)

    logs = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs, action_filter=action_filter, entity_filter=entity_filter)
