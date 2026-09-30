from flask import Blueprint, render_template, session
from models import db
from models.credential import Credential
from routes import login_required
from services.security_service import calculate_vault_security_score, analyze_password_strength
from services.encryption import decrypt_password

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']
    
    # Calculate security metrics
    security_info = calculate_vault_security_score(user_id)
    
    # Get all credentials for counts
    user_credentials = Credential.query.filter_by(user_id=user_id).all()
    total_credentials = len(user_credentials)
    favorites_count = sum(1 for c in user_credentials if c.is_favorite)
    
    # Category counts
    category_counts = {}
    for cat in Credential.CATEGORIES:
        category_counts[cat] = sum(1 for c in user_credentials if c.category == cat)
        
    # Recently added (by created_at)
    recently_added = Credential.query.filter_by(user_id=user_id)\
        .order_by(Credential.created_at.desc()).limit(5).all()

    # Recently updated / accessed
    recently_updated = Credential.query.filter_by(user_id=user_id)\
        .order_by(Credential.updated_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           security_info=security_info,
                           total_credentials=total_credentials,
                           favorites_count=favorites_count,
                           category_counts=category_counts,
                           recently_added=recently_added,
                           recently_updated=recently_updated)
