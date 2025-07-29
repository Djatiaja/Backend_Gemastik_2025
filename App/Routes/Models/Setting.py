from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Settings(db.Model):
    __tablename__ = 'settings'

    settings_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    gender_voice = db.Column(db.String(50), nullable=False)
    provider_voice = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define one-to-one relationship with User
    user = db.relationship('User', backref=db.backref('settings', uselist=False))

    def __repr__(self):
        return f'<Settings settings_id={self.settings_id} user_id={self.user_id}>'