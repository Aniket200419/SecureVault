from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from models.user import User
from models.credential import Credential
from models.login_attempt import LoginAttempt
from routes import login_required
from services.security_service import (
    calculate_vault_security_score,
    detect_password_reuse,
    analyze_password_strength,
    log_activity
)
from services.encryption import decrypt_password, encrypt_password

security_bp = Blueprint('security', __name__)

@security_bp.route('/security')
@login_required
def index():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    security_info = calculate_vault_security_score(user_id)
    reused_map = detect_password_reuse(user_id)
    
    # Process reused passwords into human-friendly representation (without raw passwords shown)
    reused_clusters = []
    for plain_pwd, creds in reused_map.items():
        reused_clusters.append({
            'count': len(creds),
            'websites': [c.website_name for c in creds],
            'credentials': creds
        })
        
    # Get weak credentials list
    user_credentials = Credential.query.filter_by(user_id=user_id).all()
    weak_credentials = []
    for cred in user_credentials:
        plain = decrypt_password(cred.encrypted_password)
        analysis = analyze_password_strength(plain)
        if analysis['rating'] == 'Weak':
            weak_credentials.append({
                'credential': cred,
                'analysis': analysis
            })

    # Recent login attempts for user
    login_attempts = LoginAttempt.query.filter(
        (LoginAttempt.user_id == user_id) | (LoginAttempt.username == user.username)
    ).order_by(LoginAttempt.created_at.desc()).limit(10).all()

    return render_template('security.html',
                           security_info=security_info,
                           reused_clusters=reused_clusters,
                           weak_credentials=weak_credentials,
                           login_attempts=login_attempts,
                           user=user)


@security_bp.route('/security/change-master-password', methods=['GET', 'POST'])
@login_required
def change_master_password():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_new_password = request.form.get('confirm_new_password', '')

        if not current_password or not new_password or not confirm_new_password:
            flash('All password fields are required.', 'danger')
            return render_template('security_change_password.html')

        if not user.check_password(current_password):
            log_activity(db, user_id, "Failed Master Password Change (Invalid Current Password)")
            flash('Current master password is incorrect.', 'danger')
            return render_template('security_change_password.html')

        if new_password != confirm_new_password:
            flash('New master password and confirmation do not match.', 'danger')
            return render_template('security_change_password.html')

        strength = analyze_password_strength(new_password)
        if strength['rating'] == 'Weak':
            flash('New master password is too weak. Please choose a stronger password.', 'danger')
            return render_template('security_change_password.html')

        # Update master password hash
        user.set_password(new_password)
        db.session.commit()

        log_activity(db, user_id, "Master Password Changed Successfully")
        flash('Master password updated successfully!', 'success')
        return redirect(url_for('security.index'))

    return render_template('security_change_password.html')


@security_bp.route('/generator')
@login_required
def generator():
    return render_template('generator.html')


@security_bp.route('/favorites')
@login_required
def favorites():
    user_id = session['user_id']
    fav_credentials = Credential.query.filter_by(user_id=user_id, is_favorite=True)\
        .order_by(Credential.website_name.asc()).all()

    processed = []
    for cred in fav_credentials:
        plain_pwd = decrypt_password(cred.encrypted_password)
        strength = analyze_password_strength(plain_pwd)
        processed.append({
            'id': cred.id,
            'website_name': cred.website_name,
            'website_url': cred.website_url,
            'username': cred.username,
            'category': cred.category,
            'notes': cred.notes,
            'is_favorite': cred.is_favorite,
            'created_at': cred.created_at,
            'updated_at': cred.updated_at,
            'strength': strength
        })

    return render_template('favorites.html', credentials=processed)
