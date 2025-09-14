from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

# Import configurations and models
from config import Config
from models import db, User, Document, Template, Payment, Admin, Analytics

# Import route blueprints
from auth import auth_bp
from tools import tools_bp
from admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tools_bp, url_prefix='/tools')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['GENERATED_FILES_FOLDER'], exist_ok=True)
    
    with app.app_context():
        # Create tables
        db.create_all()

        # Create default admin user
        admin = Admin.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
        if not admin:
            admin = Admin(
                email=app.config['ADMIN_EMAIL'],
                full_name='System Administrator',
                is_super_admin=True
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)

            # Create default templates
            default_templates = [
                {'name': 'Modern Invoice', 'document_type': 'invoice', 'is_premium': False},
                {'name': 'Corporate Invoice', 'document_type': 'invoice', 'is_premium': True},
                {'name': 'Professional Resume', 'document_type': 'resume', 'is_premium': False},
                {'name': 'Creative Resume', 'document_type': 'resume', 'is_premium': True},
                {'name': 'Achievement Certificate', 'document_type': 'certificate', 'is_premium': False},
                {'name': 'Completion Certificate', 'document_type': 'certificate', 'is_premium': True},
            ]

            for template_data in default_templates:
                template = Template(**template_data)
                db.session.add(template)

            db.session.commit()

    # Register main routes
    @app.route('/')
    def index():
        # Update daily analytics
        Analytics.update_daily_stats()

        # Get tool statistics
        tool_stats = {
            'total_documents': Document.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'popular_tools': db.session.query(
                Document.document_type,
                db.func.count(Document.id).label('count')
            ).group_by(Document.document_type).order_by(db.text('count DESC')).limit(4).all()
        }

        return render_template('index.html', stats=tool_stats)

    @app.route('/dashboard')
    def dashboard():
        if not is_logged_in():
            flash('Please login to access dashboard', 'warning')
            return redirect(url_for('auth.login'))

        user = get_current_user()
        documents = Document.query.filter_by(user_id=user.id).order_by(Document.created_at.desc()).all()

        # Group documents by type
        doc_stats = {}
        for doc in documents:
            if doc.document_type not in doc_stats:
                doc_stats[doc.document_type] = 0
            doc_stats[doc.document_type] += 1

        return render_template('dashboard.html',
                             user=user,
                             documents=documents,
                             doc_stats=doc_stats)

    @app.route('/profile')
    def profile():
        if not is_logged_in():
            flash('Please login to access profile', 'warning')
            return redirect(url_for('auth.login'))

        user = get_current_user()
        return render_template('profile.html', user=user)

    @app.route('/pricing')
    def pricing():
        plans = app.config['SUBSCRIPTION_PLANS']
        return render_template('pricing.html', plans=plans)

    @app.route('/download/<document_uuid>')
    def download_document(document_uuid):
        if not is_logged_in():
            flash('Please login to download documents', 'warning')
            return redirect(url_for('auth.login'))

        user = get_current_user()
        document = Document.query.filter_by(uuid=document_uuid, user_id=user.id).first()

        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('dashboard'))

        # Update download count
        document.downloaded_count += 1
        db.session.commit()

        try:
            return send_file(document.file_path, as_attachment=True,
                            download_name=f"{document.title}.{document.file_type}")
        except FileNotFoundError:
            flash('File not found on server', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/api/user/stats')
    def api_user_stats():
        if not is_logged_in():
            return jsonify({'error': 'Not authenticated'}), 401

        user = get_current_user()
        stats = {
            'documents_created': user.documents_created,
            'subscription_plan': user.subscription_plan,
            'is_premium': user.is_premium(),
            'can_create_document': user.can_create_document(),
            'documents_this_month': Document.query.filter(
                Document.user_id == user.id,
                Document.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ).count()
        }
        return jsonify(stats)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html',
                             error_code=404,
                             error_message="Page not found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html',
                             error_code=500,
                             error_message="Internal server error"), 500

    return app

app = create_app()

# Helper function to check if user is logged in
def is_logged_in():
    return 'user_id' in session

def get_current_user():
    if is_logged_in():
        return User.query.get(session['user_id'])
    return None

# Context processors
@app.context_processor
def inject_user():
    return dict(
        current_user=get_current_user(),
        is_logged_in=is_logged_in()
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
