from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from models.user import User
from models.activity import ActivityLog
from routes import login_required
from services.security_service import log_activity, calculate_vault_security_score

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()

        if not full_name or not email or not username:
            flash('All profile fields are required.', 'danger')
            return render_template('profile.html', user=user)

        # Check unique constraints if changed
        if email != user.email:
            existing_email = User.query.filter(User.email == email, User.id != user_id).first()
            if existing_email:
                flash('Email address is already in use by another account.', 'danger')
                return render_template('profile.html', user=user)

        if username != user.username:
            existing_username = User.query.filter(User.username == username, User.id != user_id).first()
            if existing_username:
                flash('Username is already taken by another account.', 'danger')
                return render_template('profile.html', user=user)

        user.full_name = full_name
        user.email = email
        user.username = username
        db.session.commit()

        session['full_name'] = user.full_name
        session['username'] = user.username

        log_activity(db, user_id, "Updated Profile Details")
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))

    # Security score summary for profile display
    security_info = calculate_vault_security_score(user_id)

    # Activity logs for user
    user_logs = ActivityLog.query.filter_by(user_id=user_id)\
        .order_by(ActivityLog.created_at.desc()).limit(20).all()

    return render_template('profile.html', user=user, security_info=security_info, logs=user_logs)
