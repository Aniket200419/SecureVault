from flask import Blueprint, request, jsonify, session
from models import db
from models.credential import Credential
from routes import login_required
from services.password_generator import generate_password
from services.security_service import analyze_password_strength, calculate_vault_security_score
from services.encryption import decrypt_password

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/password/generate', methods=['POST'])
def generate_api():
    data = request.get_json() or {}
    length = data.get('length', 16)
    use_upper = data.get('uppercase', True)
    use_lower = data.get('lowercase', True)
    use_num = data.get('numbers', True)
    use_sym = data.get('symbols', True)

    pwd = generate_password(
        length=length,
        use_uppercase=use_upper,
        use_lowercase=use_lower,
        use_numbers=use_num,
        use_symbols=use_sym
    )

    strength = analyze_password_strength(pwd)

    return jsonify({
        'status': 'success',
        'password': pwd,
        'strength': strength
    })


@api_bp.route('/api/password/strength', methods=['POST'])
def strength_api():
    data = request.get_json() or {}
    pwd = data.get('password', '')
    strength = analyze_password_strength(pwd)
    return jsonify({
        'status': 'success',
        'strength': strength
    })


@api_bp.route('/api/vault/search')
@login_required
def search_api():
    user_id = session['user_id']
    query = request.args.get('q', '').strip().lower()

    credentials = Credential.query.filter_by(user_id=user_id).all()
    results = []

    for cred in credentials:
        if query:
            if not (query in cred.website_name.lower() or
                    query in (cred.username or '').lower() or
                    query in (cred.category or '').lower() or
                    query in (cred.website_url or '').lower()):
                continue

        plain_pwd = decrypt_password(cred.encrypted_password)
        strength = analyze_password_strength(plain_pwd)

        results.append({
            'id': cred.id,
            'website_name': cred.website_name,
            'website_url': cred.website_url,
            'username': cred.username,
            'category': cred.category,
            'is_favorite': cred.is_favorite,
            'updated_at': cred.updated_at.strftime('%Y-%m-%d %H:%M') if cred.updated_at else '',
            'strength_rating': strength['rating'],
            'strength_score': strength['score']
        })

    return jsonify({
        'status': 'success',
        'count': len(results),
        'credentials': results
    })


@api_bp.route('/api/security/score')
@login_required
def security_score_api():
    user_id = session['user_id']
    security_info = calculate_vault_security_score(user_id)
    return jsonify({
        'status': 'success',
        'security': security_info
    })
