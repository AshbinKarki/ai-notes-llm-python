from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    notes = db.relationship("Note", backref="user", lazy=True)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Note(db.Model):
    __tablename__ = "notes"

    note_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.user_id"), nullable=False)

    topic = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    last_update = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "note_id": self.note_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "message": self.message,
            "last_update": self.last_update.isoformat(),
        }
