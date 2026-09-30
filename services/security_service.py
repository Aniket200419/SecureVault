import re
from datetime import datetime, timezone, timedelta
from flask import request
from models.activity import ActivityLog
from models.login_attempt import LoginAttempt
from models.credential import Credential
from services.encryption import decrypt_password

COMMON_WEAK_PASSWORDS = {
    '123456', 'password', '12345678', 'qwerty', '123456789', '12345', '1234', 
    '111111', '1234567', 'dragon', 'welcome', 'admin', 'password1', 'master',
    'letmein', 'monkey', 'shadow', 'sunshine', '123123', 'pass123', 'admin123'
}

def analyze_password_strength(password: str) -> dict:
    """Analyze password strength using metrics, rules, and dictionary checks."""
    if not password:
        return {
            'score': 0,
            'rating': 'Weak',
            'checks': {
                'has_length': False,
                'has_uppercase': False,
                'has_lowercase': False,
                'has_number': False,
                'has_special': False,
                'not_common': True
            }
        }
        
    length_score = 0
    if len(password) >= 16:
        length_score = 30
    elif len(password) >= 12:
        length_score = 25
    elif len(password) >= 8:
        length_score = 15
    else:
        length_score = 5

    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_num = bool(re.search(r'[0-9]', password))
    has_spec = bool(re.search(r'[^A-Za-z0-9]', password))
    not_common = password.lower() not in COMMON_WEAK_PASSWORDS

    char_score = 0
    if has_upper: char_score += 15
    if has_lower: char_score += 15
    if has_num: char_score += 20
    if has_spec: char_score += 20

    total_score = length_score + char_score
    if not not_common:
        total_score = min(total_score, 20)

    total_score = min(100, max(0, total_score))

    if total_score >= 80:
        rating = "Very Strong"
    elif total_score >= 60:
        rating = "Strong"
    elif total_score >= 40:
        rating = "Medium"
    else:
        rating = "Weak"

    return {
        'score': total_score,
        'rating': rating,
        'checks': {
            'has_length': len(password) >= 8,
            'has_uppercase': has_upper,
            'has_lowercase': has_lower,
            'has_number': has_num,
            'has_special': has_spec,
            'not_common': not_common
        }
    }

def detect_password_reuse(user_id: int):
    """
    Detect credentials sharing identical decrypted passwords for a given user.
    Returns dictionary mapping decrypted password (masked/hashed for safety) -> list of credentials.
    """
    user_credentials = Credential.query.filter_by(user_id=user_id).all()
    password_map = {}
    
    for cred in user_credentials:
        plain_pwd = decrypt_password(cred.encrypted_password)
        if not plain_pwd or plain_pwd == "[Decryption Error]":
            continue
        if plain_pwd not in password_map:
            password_map[plain_pwd] = []
        password_map[plain_pwd].append(cred)
        
    reused = {}
    for pwd, creds in password_map.items():
        if len(creds) > 1:
            reused[pwd] = creds
            
    return reused

def calculate_vault_security_score(user_id: int) -> dict:
    """Calculate aggregate vault security metrics, warnings, and overall score."""
    user_credentials = Credential.query.filter_by(user_id=user_id).all()
    total = len(user_credentials)
    
    if total == 0:
        return {
            'overall_score': 100,
            'total_credentials': 0,
            'strong_count': 0,
            'weak_count': 0,
            'reused_count': 0,
            'old_count': 0,
            'alerts': ["Your vault is empty. Add credentials to begin monitoring your security!"]
        }
        
    strong_count = 0
    weak_count = 0
    reused_creds_set = set()
    old_count = 0
    now = datetime.now(timezone.utc)
    ninety_days_ago = now - timedelta(days=90)
    
    # Check reuse
    reused_map = detect_password_reuse(user_id)
    for pwd, creds in reused_map.items():
        for c in creds:
            reused_creds_set.add(c.id)
            
    for cred in user_credentials:
        plain_pwd = decrypt_password(cred.encrypted_password)
        analysis = analyze_password_strength(plain_pwd)
        
        if analysis['rating'] in ['Strong', 'Very Strong']:
            strong_count += 1
        elif analysis['rating'] == 'Weak':
            weak_count += 1
            
        # Old password check (> 90 days)
        updated_dt = cred.updated_at
        if updated_dt and updated_dt.tzinfo is None:
            updated_dt = updated_dt.replace(tzinfo=timezone.utc)
            
        if updated_dt and updated_dt < ninety_days_ago:
            old_count += 1
            
    reused_count = len(reused_creds_set)
    
    # Calculate score penalty
    # Base 100
    # Penalty: weak passwords (-15 each), reused passwords (-10 each), old passwords (-5 each)
    score = 100 - (weak_count * 15) - (reused_count * 10) - (old_count * 5)
    overall_score = min(100, max(15, score))
    
    alerts = []
    if weak_count > 0:
        alerts.append(f"Security Warning: You have {weak_count} weak password(s) in your vault.")
    if reused_count > 0:
        alerts.append(f"Security Alert: You are reusing passwords across {reused_count} account(s).")
    if old_count > 0:
        alerts.append(f"Notice: {old_count} credential(s) have not been updated in over 90 days.")
    if not alerts:
        alerts.append("Great job! Your password vault meets high security standards.")
        
    return {
        'overall_score': overall_score,
        'total_credentials': total,
        'strong_count': strong_count,
        'weak_count': weak_count,
        'reused_count': reused_count,
        'old_count': old_count,
        'alerts': alerts
    }

def log_activity(db, user_id, action, ip_address=None, user_agent=None):
    """Log user activity into activity_logs table."""
    try:
        if not ip_address:
            ip_address = request.remote_addr if request else '127.0.0.1'
        if not user_agent:
            user_agent = str(request.user_agent)[:250] if request else 'System'
            
        log_entry = ActivityLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

def record_login_attempt(db, username, success, user_id=None, ip_address=None):
    """Record login attempt in login_attempts table."""
    try:
        if not ip_address:
            ip_address = request.remote_addr if request else '127.0.0.1'
            
        attempt = LoginAttempt(
            user_id=user_id,
            username=username,
            success=success,
            ip_address=ip_address
        )
        db.session.add(attempt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
