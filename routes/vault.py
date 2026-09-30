from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db
from models.credential import Credential
from routes import login_required
from services.encryption import encrypt_password, decrypt_password
from services.security_service import analyze_password_strength, log_activity

vault_bp = Blueprint('vault', __name__)

@vault_bp.route('/vault')
@login_required
def index():
    user_id = session['user_id']
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('filter', 'all')
    query = request.args.get('q', '').strip()

    q_builder = Credential.query.filter_by(user_id=user_id)

    if category_filter and category_filter in Credential.CATEGORIES:
        q_builder = q_builder.filter_by(category=category_filter)

    if status_filter == 'favorites':
        q_builder = q_builder.filter_by(is_favorite=True)

    credentials = q_builder.order_by(Credential.website_name.asc()).all()

    # Dynamic post-processing for search & strength filters
    processed_credentials = []
    for cred in credentials:
        plain_pwd = decrypt_password(cred.encrypted_password)
        strength = analyze_password_strength(plain_pwd)
        
        # Search filter
        if query:
            q_lower = query.lower()
            if not (q_lower in cred.website_name.lower() or
                    q_lower in (cred.username or '').lower() or
                    q_lower in (cred.category or '').lower() or
                    q_lower in (cred.website_url or '').lower()):
                continue

        # Strength filter
        if status_filter == 'weak' and strength['rating'] != 'Weak':
            continue
        elif status_filter == 'strong' and strength['rating'] not in ['Strong', 'Very Strong']:
            continue
        elif status_filter == 'recent':
            # sort handled below
            pass

        processed_credentials.append({
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

    if status_filter == 'recent':
        processed_credentials.sort(key=lambda x: x['created_at'], reverse=True)

    return render_template('vault.html',
                           credentials=processed_credentials,
                           categories=Credential.CATEGORIES,
                           selected_category=category_filter,
                           selected_filter=status_filter,
                           search_query=query)


@vault_bp.route('/vault/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        website_name = request.form.get('website_name', '').strip()
        website_url = request.form.get('website_url', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        category = request.form.get('category', 'Other')
        notes = request.form.get('notes', '').strip()
        is_favorite = bool(request.form.get('is_favorite'))

        if not website_name or not username or not password:
            flash('Website name, username/email, and password are required fields.', 'danger')
            return render_template('add_password.html',
                                   categories=Credential.CATEGORIES,
                                   website_name=website_name,
                                   website_url=website_url,
                                   username=username,
                                   category=category,
                                   notes=notes)

        # Encrypt password before storing
        encrypted_pwd = encrypt_password(password)

        new_credential = Credential(
            user_id=session['user_id'],
            website_name=website_name,
            website_url=website_url if website_url else None,
            username=username,
            encrypted_password=encrypted_pwd,
            category=category if category in Credential.CATEGORIES else 'Other',
            notes=notes if notes else None,
            is_favorite=is_favorite
        )

        db.session.add(new_credential)
        db.session.commit()

        log_activity(db, session['user_id'], f"Created Credential for '{website_name}'")
        flash(f"Credential for '{website_name}' saved securely!", 'success')
        return redirect(url_for('vault.index'))

    return render_template('add_password.html', categories=Credential.CATEGORIES)


@vault_bp.route('/vault/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    cred = Credential.query.filter_by(id=id, user_id=session['user_id']).first_or_404()

    if request.method == 'POST':
        website_name = request.form.get('website_name', '').strip()
        website_url = request.form.get('website_url', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        category = request.form.get('category', 'Other')
        notes = request.form.get('notes', '').strip()
        is_favorite = bool(request.form.get('is_favorite'))

        if not website_name or not username:
            flash('Website name and username/email are required.', 'danger')
            return render_template('edit_password.html', credential=cred, categories=Credential.CATEGORIES)

        cred.website_name = website_name
        cred.website_url = website_url if website_url else None
        cred.username = username
        cred.category = category if category in Credential.CATEGORIES else 'Other'
        cred.notes = notes if notes else None
        cred.is_favorite = is_favorite

        # If a new password was typed, re-encrypt it
        if password:
            cred.encrypted_password = encrypt_password(password)

        cred.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        log_activity(db, session['user_id'], f"Updated Credential for '{website_name}'")
        flash(f"Credential for '{website_name}' updated successfully!", 'success')
        return redirect(url_for('vault.index'))

    # Decrypt existing password for editing view
    decrypted_pwd = decrypt_password(cred.encrypted_password)

    return render_template('edit_password.html',
                           credential=cred,
                           decrypted_password=decrypted_pwd,
                           categories=Credential.CATEGORIES)


@vault_bp.route('/vault/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    cred = Credential.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    website_name = cred.website_name

    db.session.delete(cred)
    db.session.commit()

    log_activity(db, session['user_id'], f"Deleted Credential for '{website_name}'")
    flash(f"Credential for '{website_name}' removed from vault.", 'info')
    return redirect(url_for('vault.index'))


@vault_bp.route('/vault/toggle-favorite/<int:id>', methods=['POST'])
@login_required
def toggle_favorite(id):
    cred = Credential.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    cred.is_favorite = not cred.is_favorite
    db.session.commit()

    action_str = "Favorited" if cred.is_favorite else "Unfavorited"
    log_activity(db, session['user_id'], f"{action_str} Credential '{cred.website_name}'")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'is_favorite': cred.is_favorite})

    return redirect(request.referrer or url_for('vault.index'))


@vault_bp.route('/vault/decrypt/<int:id>', methods=['GET', 'POST'])
@login_required
def decrypt_api(id):
    cred = Credential.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    plain_password = decrypt_password(cred.encrypted_password)

    # Log viewing of password (never log actual password value)
    log_activity(db, session['user_id'], f"Revealed Password for '{cred.website_name}'")

    return jsonify({
        'status': 'success',
        'password': plain_password
    })
