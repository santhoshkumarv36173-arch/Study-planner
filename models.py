from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    plans = db.relationship('StudyPlan', backref='user', lazy=True, cascade='all, delete-orphan')

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subjects = db.Column(db.String(500), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('PlanTask', backref='plan', lazy=True, cascade='all, delete-orphan')

    @property
    def progress(self):
        total = len(self.tasks)
        if total == 0:
            return 0
        completed = sum(1 for t in self.tasks if t.completed)
        return round((completed / total) * 100)

class PlanTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    time_slot = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    task_type = db.Column(db.String(20), nullable=False)
    completed = db.Column(db.Boolean, default=False)