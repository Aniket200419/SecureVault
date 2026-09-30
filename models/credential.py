from datetime import datetime, timezone
from models import db

class Credential(db.Model):
    __tablename__ = 'credentials'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    website_name = db.Column(db.String(100), nullable=False)
    website_url = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(120), nullable=False)
    encrypted_password = db.Column(db.String(512), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    notes = db.Column(db.Text, nullable=True)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    CATEGORIES = [
        'Social Media',
        'Banking',
        'Email',
        'Education',
        'Work',
        'Shopping',
        'Entertainment',
        'Other'
    ]

    def __repr__(self):
        return f'<Credential {self.website_name} ({self.username})>'
