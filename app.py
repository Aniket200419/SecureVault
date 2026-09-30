import os
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db
from models.user import User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.vault import vault_bp
from routes.security import security_bp
from routes.profile import profile_bp
from routes.admin import admin_bp
from routes.api import api_bp

csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Exempt API blueprint from CSRF for easy JSON integration where needed
    csrf.exempt(api_bp)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vault_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Root route redirect
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Custom Jinja Filters
    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        if not dt:
            return "Never"
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"

    @app.template_filter('category_badge')
    def category_badge_filter(category):
        badges = {
            'Social Media': 'bg-info text-dark',
            'Banking': 'bg-warning text-dark',
            'Email': 'bg-primary',
            'Education': 'bg-purple text-white',
            'Work': 'bg-secondary',
            'Shopping': 'bg-success',
            'Entertainment': 'bg-danger',
            'Other': 'bg-dark text-light border border-secondary'
        }
        return badges.get(category, 'bg-secondary')

    # Error Handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto DB tables creation and Admin user seeding
    with app.app_context():
        db.create_all()
        # Seed default Admin account if no admin exists
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin = User(
                full_name='System Administrator',
                email='admin@securevault.io',
                username='admin',
                role='admin',
                is_active=True
            )
            admin.set_password('Admin@123456')
            db.session.add(admin)
            db.session.commit()
            print("[SecureVault] Default Admin seeded: username='admin', password='Admin@123456'")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
