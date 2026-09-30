from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from models.user import User
from services.security_service import analyze_password_strength, log_activity, record_login_attempt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name or not email or not username or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, username=username)

        if password != confirm_password:
            flash('Master password and confirmation do not match.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, username=username)

        # Check unique constraints
        if User.query.filter_by(email=email).first():
            flash('Email address is already registered.', 'danger')
            return render_template('auth/register.html', full_name=full_name, username=username)

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email)

        # Master password strength check
        strength = analyze_password_strength(password)
        if strength['rating'] == 'Weak':
            flash('Master password is too weak. Must be at least 8 characters and contain letters, numbers, or symbols.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, username=username)

        # Create user
        new_user = User(
            full_name=full_name,
            email=email,
            username=username,
            role='user'
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        log_activity(db, new_user.id, "User Registered Account")
        flash('Registration successful! You can now log in with your master password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not login_input or not password:
            flash('Please provide both username/email and master password.', 'danger')
            return render_template('auth/login.html')

        # Find user by email or username
        user = User.query.filter((User.email == login_input) | (User.username == login_input)).first()

        if not user or not user.check_password(password):
            record_login_attempt(db, login_input, success=False, user_id=user.id if user else None)
            log_activity(db, user.id if user else None, f"Failed Login Attempt for '{login_input}'")
            flash('Invalid username/email or master password.', 'danger')
            return render_template('auth/login.html', login_input=login_input)

        if not user.is_active:
            record_login_attempt(db, login_input, success=False, user_id=user.id)
            log_activity(db, user.id, "Attempted Login on Deactivated Account")
            flash('Your account has been deactivated. Please contact support/administrator.', 'danger')
            return render_template('auth/login.html')

        # Successful login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        record_login_attempt(db, login_input, success=True, user_id=user.id)
        log_activity(db, user.id, "User Logged In")

        session.permanent = remember
        session['user_id'] = user.id
        session['username'] = user.username
        session['full_name'] = user.full_name
        session['role'] = user.role

        flash(f'Welcome back, {user.full_name}!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_activity(db, user_id, "User Logged Out")
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))
