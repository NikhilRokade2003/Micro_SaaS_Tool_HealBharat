from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    subscription_plan = db.Column(db.String(20), default='free')
    subscription_expires = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    documents_created = db.Column(db.Integer, default=0)
    
    # Relationships
    documents = db.relationship('Document', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_premium(self):
        if self.subscription_plan == 'premium':
            if self.subscription_expires and self.subscription_expires > datetime.utcnow():
                return True
        return False
    
    def can_create_document(self):
        if self.is_premium():
            return True
        # Free users limited to 5 documents per month
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_docs = Document.query.filter(
            Document.user_id == self.id,
            Document.created_at >= current_month_start
        ).count()
        return monthly_docs < 5
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'subscription_plan': self.subscription_plan,
            'is_premium': self.is_premium(),
            'documents_created': self.documents_created,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(20), nullable=False)  # invoice, resume, certificate, qrcode
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, docx, png, svg
    template_used = db.Column(db.String(50), nullable=True)
    data_json = db.Column(db.Text, nullable=True)  # Store form data as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    downloaded_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'document_type': self.document_type,
            'title': self.title,
            'file_type': self.file_type,
            'template_used': self.template_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'downloaded_count': self.downloaded_count
        }

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    document_type = db.Column(db.String(20), nullable=False)
    template_file = db.Column(db.String(200), nullable=True)
    preview_image = db.Column(db.String(200), nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'document_type': self.document_type,
            'is_premium': self.is_premium,
            'is_active': self.is_active,
            'usage_count': self.usage_count
        }

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_id = db.Column(db.String(100), nullable=False)
    order_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(db.String(20), nullable=False)  # pending, completed, failed
    payment_method = db.Column(db.String(20), nullable=False)  # razorpay, stripe
    subscription_months = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'amount': self.amount,
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    active_users = db.Column(db.Integer, default=0)
    documents_created = db.Column(db.Integer, default=0)
    tool_usage = db.Column(db.Text, nullable=True)  # JSON string
    revenue = db.Column(db.Float, default=0.0)
    
    @staticmethod
    def update_daily_stats():
        today = datetime.utcnow().date()
        analytics = Analytics.query.filter_by(date=today).first()
        if not analytics:
            analytics = Analytics(date=today)
            db.session.add(analytics)
        
        # Update stats
        analytics.active_users = User.query.filter(
            User.last_login >= datetime.combine(today, datetime.min.time())
        ).count()
        
        analytics.documents_created = Document.query.filter(
            Document.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        db.session.commit()
        return analytics