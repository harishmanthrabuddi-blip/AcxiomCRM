from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.extensions import db
from app.models import User, Role
from app.forms import LoginForm, RegisterForm

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user:
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)

            if user.is_locked_out():
                flash('Account is temporarily locked due to repeated failed login attempts. Please try again later.', 'danger')
                return render_template('auth/login.html', form=form)

            if user.check_password(form.password.data):
                user.reset_failed_login()
                login_user(user, remember=form.remember_me.data)
                flash(f'Welcome back, {user.name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.index'))
            else:
                user.record_failed_login(max_attempts=5, lockout_minutes=15)
                if user.is_locked_out():
                    flash('Account has been locked for 15 minutes due to 5 consecutive failed login attempts.', 'danger')
                else:
                    attempts_left = 5 - user.failed_login_count
                    flash(f'Invalid email or password. {attempts_left} attempt(s) remaining before account lockout.', 'warning')
        else:
            flash('Invalid email or password.', 'warning')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    roles = Role.query.all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role_id=form.role_id.data,
            is_active=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)
