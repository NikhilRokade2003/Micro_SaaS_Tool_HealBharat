from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app, send_file
from models import db, User, Document, Template, Payment, Admin, Analytics
from datetime import datetime, timedelta
import json
import csv
import os
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login as admin to access this page.', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_current_admin():
    if 'admin_id' in session:
        return Admin.query.get(session['admin_id'])
    return None

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('admin/login.html')
    
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash('Please enter both email and password.', 'danger')
        return render_template('admin/login.html', email=email)
    
    admin = Admin.query.filter_by(email=email).first()
    
    if not admin or not admin.check_password(password):
        flash('Invalid email or password.', 'danger')
        return render_template('admin/login.html', email=email)
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create admin session
    session['admin_id'] = admin.id
    session['admin_email'] = admin.email
    session['admin_name'] = admin.full_name
    
    flash(f'Welcome back, {admin.full_name}!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Update daily stats
    Analytics.update_daily_stats()
    
    # Get key metrics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    premium_users = User.query.filter_by(subscription_plan='premium').count()
    total_documents = Document.query.count()
    
    # Documents created today
    today = datetime.utcnow().date()
    documents_today = Document.query.filter(
        Document.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    # Revenue this month (mock data for demo)
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_this_month = Payment.query.filter(
        Payment.completed_at >= current_month_start,
        Payment.status == 'completed'
    ).with_entities(db.func.sum(Payment.amount)).scalar() or 0
    
    # Most used tools
    tool_usage = db.session.query(
        Document.document_type,
        db.func.count(Document.id).label('count')
    ).group_by(Document.document_type).order_by(db.text('count DESC')).all()
    
    # Recent registrations (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = User.query.filter(
        User.created_at >= week_ago
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Daily active users for the past 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        analytics = Analytics.query.filter_by(date=date).first()
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'active_users': analytics.active_users if analytics else 0,
            'documents_created': analytics.documents_created if analytics else 0
        })
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'premium_users': premium_users,
        'total_documents': total_documents,
        'documents_today': documents_today,
        'revenue_this_month': revenue_this_month,
        'tool_usage': tool_usage,
        'recent_users': recent_users,
        'daily_stats': daily_stats
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_plan = request.args.get('plan', '')
    filter_status = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.email.contains(search),
                User.full_name.contains(search)
            )
        )
    
    if filter_plan:
        query = query.filter_by(subscription_plan=filter_plan)
    
    if filter_status == 'active':
        query = query.filter_by(is_active=True)
    elif filter_status == 'inactive':
        query = query.filter_by(is_active=False)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', 
                         users=users, 
                         search=search,
                         filter_plan=filter_plan,
                         filter_status=filter_status)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.email} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/details')
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    documents = Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc()).all()
    payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
    
    return render_template('admin/user_details.html', 
                         user=user, 
                         documents=documents, 
                         payments=payments)

@admin_bp.route('/templates')
@admin_required
def templates():
    templates = Template.query.order_by(Template.created_at.desc()).all()
    return render_template('admin/templates.html', templates=templates)

@admin_bp.route('/templates/create', methods=['GET', 'POST'])
@admin_required
def create_template():
    if request.method == 'GET':
        return render_template('admin/template_form.html')
    
    name = request.form.get('name')
    document_type = request.form.get('document_type')
    is_premium = request.form.get('is_premium') == 'on'
    
    if not name or not document_type:
        flash('Please fill in all required fields.', 'danger')
        return render_template('admin/template_form.html', 
                             name=name, 
                             document_type=document_type,
                             is_premium=is_premium)
    
    template = Template(
        name=name,
        document_type=document_type,
        is_premium=is_premium
    )
    
    db.session.add(template)
    db.session.commit()
    
    flash('Template created successfully!', 'success')
    return redirect(url_for('admin.templates'))

@admin_bp.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template(template_id):
    template = Template.query.get_or_404(template_id)
    
    if request.method == 'GET':
        return render_template('admin/template_form.html', template=template)
    
    template.name = request.form.get('name')
    template.document_type = request.form.get('document_type')
    template.is_premium = request.form.get('is_premium') == 'on'
    template.is_active = request.form.get('is_active') == 'on'
    
    db.session.commit()
    flash('Template updated successfully!', 'success')
    return redirect(url_for('admin.templates'))

@admin_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@admin_required
def delete_template(template_id):
    template = Template.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    
    flash('Template deleted successfully!', 'success')
    return redirect(url_for('admin.templates'))

@admin_bp.route('/reports')
@admin_required
def reports():
    # Date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # User registrations by date
    user_registrations = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_datetime,
        User.created_at < end_datetime
    ).group_by(db.func.date(User.created_at)).all()
    
    # Documents created by date and type
    document_stats = db.session.query(
        db.func.date(Document.created_at).label('date'),
        Document.document_type,
        db.func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= start_datetime,
        Document.created_at < end_datetime
    ).group_by(
        db.func.date(Document.created_at),
        Document.document_type
    ).all()
    
    # Popular templates
    popular_templates = db.session.query(
        Template.name,
        Template.document_type,
        db.func.count(Document.id).label('usage_count')
    ).join(Document, Template.id == Document.template_used.cast(db.Integer), isouter=True).filter(
        Document.created_at >= start_datetime,
        Document.created_at < end_datetime
    ).group_by(Template.id, Template.name, Template.document_type).order_by(db.text('usage_count DESC')).limit(10).all()
    
    # Revenue by month (mock data)
    revenue_data = Payment.query.filter(
        Payment.completed_at >= start_datetime,
        Payment.completed_at < end_datetime,
        Payment.status == 'completed'
    ).with_entities(
        db.func.date_trunc('month', Payment.completed_at).label('month'),
        db.func.sum(Payment.amount).label('revenue')
    ).group_by(db.func.date_trunc('month', Payment.completed_at)).all()
    
    report_data = {
        'start_date': start_date,
        'end_date': end_date,
        'user_registrations': user_registrations,
        'document_stats': document_stats,
        'popular_templates': popular_templates,
        'revenue_data': revenue_data
    }
    
    return render_template('admin/reports.html', data=report_data)

@admin_bp.route('/reports/export/<format>')
@admin_required
def export_report(format):
    # Get report data
    start_date = request.args.get('start_date', (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Get users data
    users = User.query.filter(
        User.created_at >= start_datetime,
        User.created_at < end_datetime
    ).all()
    
    if format.lower() == 'csv':
        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Email', 'Full Name', 'Subscription Plan', 'Documents Created', 'Registration Date', 'Last Login'])
        
        # Write data
        for user in users:
            writer.writerow([
                user.email,
                user.full_name,
                user.subscription_plan,
                user.documents_created,
                user.created_at.strftime('%Y-%m-%d'),
                user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never'
            ])
        
        output.seek(0)
        
        # Create file-like object
        file_data = BytesIO()
        file_data.write(output.getvalue().encode('utf-8'))
        file_data.seek(0)
        
        return send_file(
            file_data,
            as_attachment=True,
            download_name=f'users_report_{start_date}_to_{end_date}.csv',
            mimetype='text/csv'
        )
    
    elif format.lower() == 'pdf':
        # Generate PDF report
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Users Report ({start_date} to {end_date})", styles['Title'])
        story.append(title)
        story.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # Users table
        data = [['Email', 'Full Name', 'Plan', 'Documents', 'Registration']]
        for user in users:
            data.append([
                user.email,
                user.full_name,
                user.subscription_plan,
                str(user.documents_created),
                user.created_at.strftime('%Y-%m-%d')
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'users_report_{start_date}_to_{end_date}.pdf',
            mimetype='application/pdf'
        )
    
    else:
        flash('Invalid export format.', 'danger')
        return redirect(url_for('admin.reports'))

@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'premium_users': User.query.filter_by(subscription_plan='premium').count(),
        'total_documents': Document.query.count(),
        'documents_today': Document.query.filter(
            Document.created_at >= datetime.combine(datetime.utcnow().date(), datetime.min.time())
        ).count()
    }
    
    return jsonify(stats)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    admin = get_current_admin()
    
    if request.method == 'GET':
        return render_template('admin/settings.html', admin=admin)
    
    # Handle settings update
    admin.full_name = request.form.get('full_name')
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if new_password:
        if not admin.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('admin/settings.html', admin=admin)
        
        admin.set_password(new_password)
    
    db.session.commit()
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('admin.settings'))