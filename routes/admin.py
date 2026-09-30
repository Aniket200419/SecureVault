from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from models.user import User
from models.credential import Credential
from models.activity import ActivityLog
from models.login_attempt import LoginAttempt
from routes import admin_required
from services.security_service import log_activity

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_required
def index():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_credentials = Credential.query.count()
    failed_logins = LoginAttempt.query.filter_by(success=False).count()
    
    # Recent activity logs across system
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # Recent suspicious login attempts
    suspicious_attempts = LoginAttempt.query.filter_by(success=False)\
        .order_by(LoginAttempt.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           active_users=active_users,
                           total_credentials=total_credentials,
                           failed_logins=failed_logins,
                           recent_logs=recent_logs,
                           suspicious_attempts=suspicious_attempts)


@admin_bp.route('/admin/users')
@admin_required
def users():
    search_q = request.args.get('q', '').strip()
    q_builder = User.query

    if search_q:
        q_lower = f"%{search_q}%"
        q_builder = q_builder.filter(
            (User.full_name.ilike(q_lower)) |
            (User.email.ilike(q_lower)) |
            (User.username.ilike(q_lower))
        )

    all_users = q_builder.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users, search_query=search_q)


@admin_bp.route('/admin/users/toggle-status/<int:id>', methods=['POST'])
@admin_required
def toggle_user_status(id):
    user = User.query.get_or_404(id)
    current_admin_id = session['user_id']

    if user.id == current_admin_id:
        flash('You cannot deactivate your own admin account.', 'warning')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    log_activity(db, current_admin_id, f"Admin {status_str} User '{user.username}' (ID: {user.id})")
    flash(f"User '{user.username}' has been {status_str}.", 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/admin/users/toggle-role/<int:id>', methods=['POST'])
@admin_required
def toggle_user_role(id):
    user = User.query.get_or_404(id)
    current_admin_id = session['user_id']

    if user.id == current_admin_id:
        flash('You cannot change your own admin role.', 'warning')
        return redirect(url_for('admin.users'))

    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()

    log_activity(db, current_admin_id, f"Admin changed role of '{user.username}' to {user.role.upper()}")
    flash(f"User '{user.username}' role changed to {user.role.upper()}.", 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/admin/logs')
@admin_required
def logs():
    log_type = request.args.get('type', 'activity')
    
    if log_type == 'login':
        login_logs = LoginAttempt.query.order_by(LoginAttempt.created_at.desc()).limit(100).all()
        return render_template('admin/logs.html', log_type='login', login_logs=login_logs)
    else:
        activity_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
        return render_template('admin/logs.html', log_type='activity', activity_logs=activity_logs)
