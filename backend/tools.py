from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, User, Document, Template
from utils import generate_invoice_pdf, generate_resume_pdf, generate_certificate_pdf, generate_qr_code
import os
import json
import uuid
from datetime import datetime

tools_bp = Blueprint('tools', __name__)

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            flash('Please login to access this tool.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Invoice Generator Routes
@tools_bp.route('/invoice', methods=['GET', 'POST'])
@login_required
def invoice_generator():
    user = get_current_user()
    
    if request.method == 'GET':
        templates = Template.query.filter_by(document_type='invoice', is_active=True).all()
        available_templates = []
        for template in templates:
            if not template.is_premium or user.is_premium():
                available_templates.append(template)
        
        return render_template('tools/invoice.html', 
                             templates=available_templates,
                             user=user)
    
    # Handle POST request - Generate invoice
    if not user.can_create_document():
        return jsonify({
            'success': False, 
            'error': 'Document limit reached. Upgrade to premium for unlimited access.'
        }), 403
    
    data = request.get_json() if request.is_json else request.form
    
    # Extract invoice data
    invoice_data = {
        'company_name': data.get('company_name'),
        'company_address': data.get('company_address'),
        'company_email': data.get('company_email'),
        'company_phone': data.get('company_phone'),
        'client_name': data.get('client_name'),
        'client_address': data.get('client_address'),
        'client_email': data.get('client_email'),
        'invoice_number': data.get('invoice_number'),
        'invoice_date': data.get('invoice_date'),
        'due_date': data.get('due_date'),
        'items': json.loads(data.get('items', '[]')),
        'tax_rate': float(data.get('tax_rate', 0)),
        'discount': float(data.get('discount', 0)),
        'notes': data.get('notes', ''),
        'template_id': data.get('template_id')
    }
    
    try:
        # Generate PDF
        filename = f"invoice_{invoice_data['invoice_number']}_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(current_app.config['GENERATED_FILES_FOLDER'], filename)
        
        generate_invoice_pdf(invoice_data, file_path)
        
        # Save to database
        document = Document(
            user_id=user.id,
            document_type='invoice',
            title=f"Invoice #{invoice_data['invoice_number']}",
            file_path=file_path,
            file_type='pdf',
            template_used=invoice_data.get('template_id'),
            data_json=json.dumps(invoice_data)
        )
        
        db.session.add(document)
        user.documents_created += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Invoice generated successfully!',
            'download_url': url_for('download_document', document_uuid=document.uuid),
            'document_id': document.uuid
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to generate invoice: {str(e)}'
        }), 500

# QR Code Generator Routes
@tools_bp.route('/qrcode', methods=['GET', 'POST'])
@login_required
def qrcode_generator():
    user = get_current_user()
    
    if request.method == 'GET':
        return render_template('tools/qrcode.html', user=user)
    
    # Handle POST request - Generate QR code
    if not user.can_create_document():
        return jsonify({
            'success': False, 
            'error': 'Document limit reached. Upgrade to premium for unlimited access.'
        }), 403
    
    data = request.get_json() if request.is_json else request.form
    
    qr_data = {
        'type': data.get('type', 'text'),
        'content': data.get('content'),
        'size': int(data.get('size', 300)),
        'format': data.get('format', 'png'),
        'error_correction': data.get('error_correction', 'M')
    }
    
    # Handle different QR types
    if qr_data['type'] == 'wifi':
        qr_content = f"WIFI:T:{data.get('wifi_security')};S:{data.get('wifi_ssid')};P:{data.get('wifi_password')};;"
    elif qr_data['type'] == 'vcard':
        qr_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{data.get('vcard_name')}
TEL:{data.get('vcard_phone')}
EMAIL:{data.get('vcard_email')}
ORG:{data.get('vcard_org')}
END:VCARD"""
    elif qr_data['type'] == 'upi':
        qr_content = f"upi://pay?pa={data.get('upi_id')}&pn={data.get('upi_name')}&am={data.get('upi_amount')}"
    else:
        qr_content = qr_data['content']
    
    try:
        # Generate QR code
        filename = f"qrcode_{uuid.uuid4().hex[:8]}.{qr_data['format']}"
        file_path = os.path.join(current_app.config['GENERATED_FILES_FOLDER'], filename)
        
        generate_qr_code(qr_content, file_path, qr_data['size'], qr_data['format'])
        
        # Save to database
        document = Document(
            user_id=user.id,
            document_type='qrcode',
            title=f"QR Code - {qr_data['type'].title()}",
            file_path=file_path,
            file_type=qr_data['format'],
            data_json=json.dumps({**qr_data, 'content': qr_content})
        )
        
        db.session.add(document)
        user.documents_created += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'QR Code generated successfully!',
            'download_url': url_for('download_document', document_uuid=document.uuid),
            'document_id': document.uuid
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to generate QR code: {str(e)}'
        }), 500

# Resume Builder Routes
@tools_bp.route('/resume', methods=['GET', 'POST'])
@login_required
def resume_builder():
    user = get_current_user()
    
    if request.method == 'GET':
        templates = Template.query.filter_by(document_type='resume', is_active=True).all()
        available_templates = []
        for template in templates:
            if not template.is_premium or user.is_premium():
                available_templates.append(template)
        
        return render_template('tools/resume.html', 
                             templates=available_templates,
                             user=user)
    
    # Handle POST request - Generate resume
    if not user.can_create_document():
        return jsonify({
            'success': False, 
            'error': 'Document limit reached. Upgrade to premium for unlimited access.'
        }), 403
    
    data = request.get_json() if request.is_json else request.form
    
    resume_data = {
        'personal_info': {
            'full_name': data.get('full_name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'address': data.get('address'),
            'linkedin': data.get('linkedin'),
            'portfolio': data.get('portfolio')
        },
        'summary': data.get('summary'),
        'education': json.loads(data.get('education', '[]')),
        'experience': json.loads(data.get('experience', '[]')),
        'skills': json.loads(data.get('skills', '[]')),
        'projects': json.loads(data.get('projects', '[]')),
        'certifications': json.loads(data.get('certifications', '[]')),
        'template_id': data.get('template_id'),
        'format': data.get('format', 'pdf')
    }
    
    try:
        # Generate resume
        format_ext = resume_data['format']
        filename = f"resume_{resume_data['personal_info']['full_name'].replace(' ', '_')}_{uuid.uuid4().hex[:8]}.{format_ext}"
        file_path = os.path.join(current_app.config['GENERATED_FILES_FOLDER'], filename)
        
        generate_resume_pdf(resume_data, file_path)
        
        # Save to database
        document = Document(
            user_id=user.id,
            document_type='resume',
            title=f"Resume - {resume_data['personal_info']['full_name']}",
            file_path=file_path,
            file_type=format_ext,
            template_used=resume_data.get('template_id'),
            data_json=json.dumps(resume_data)
        )
        
        db.session.add(document)
        user.documents_created += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resume generated successfully!',
            'download_url': url_for('download_document', document_uuid=document.uuid),
            'document_id': document.uuid
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to generate resume: {str(e)}'
        }), 500

# Certificate Creator Routes
@tools_bp.route('/certificate', methods=['GET', 'POST'])
@login_required
def certificate_creator():
    user = get_current_user()
    
    if request.method == 'GET':
        templates = Template.query.filter_by(document_type='certificate', is_active=True).all()
        available_templates = []
        for template in templates:
            if not template.is_premium or user.is_premium():
                available_templates.append(template)
        
        return render_template('tools/certificate.html', 
                             templates=available_templates,
                             user=user)
    
    # Handle POST request - Generate certificate
    if not user.can_create_document():
        return jsonify({
            'success': False, 
            'error': 'Document limit reached. Upgrade to premium for unlimited access.'
        }), 403
    
    data = request.get_json() if request.is_json else request.form
    
    # Check if bulk generation (premium feature)
    is_bulk = data.get('bulk_mode', False)
    if is_bulk and not user.is_premium():
        return jsonify({
            'success': False,
            'error': 'Bulk certificate generation requires premium subscription.'
        }), 403
    
    certificate_data = {
        'recipient_name': data.get('recipient_name'),
        'course_name': data.get('course_name'),
        'completion_date': data.get('completion_date'),
        'instructor_name': data.get('instructor_name'),
        'organization': data.get('organization'),
        'description': data.get('description'),
        'template_id': data.get('template_id'),
        'bulk_names': json.loads(data.get('bulk_names', '[]')) if is_bulk else []
    }
    
    try:
        generated_files = []
        
        if is_bulk and certificate_data['bulk_names']:
            # Generate multiple certificates
            for name in certificate_data['bulk_names']:
                if name.strip():
                    cert_data = certificate_data.copy()
                    cert_data['recipient_name'] = name.strip()
                    
                    filename = f"certificate_{name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
                    file_path = os.path.join(current_app.config['GENERATED_FILES_FOLDER'], filename)
                    
                    generate_certificate_pdf(cert_data, file_path)
                    
                    # Save to database
                    document = Document(
                        user_id=user.id,
                        document_type='certificate',
                        title=f"Certificate - {name}",
                        file_path=file_path,
                        file_type='pdf',
                        template_used=certificate_data.get('template_id'),
                        data_json=json.dumps(cert_data)
                    )
                    
                    db.session.add(document)
                    generated_files.append({
                        'name': name,
                        'download_url': url_for('download_document', document_uuid=document.uuid)
                    })
        else:
            # Generate single certificate
            filename = f"certificate_{certificate_data['recipient_name'].replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
            file_path = os.path.join(current_app.config['GENERATED_FILES_FOLDER'], filename)
            
            generate_certificate_pdf(certificate_data, file_path)
            
            # Save to database
            document = Document(
                user_id=user.id,
                document_type='certificate',
                title=f"Certificate - {certificate_data['recipient_name']}",
                file_path=file_path,
                file_type='pdf',
                template_used=certificate_data.get('template_id'),
                data_json=json.dumps(certificate_data)
            )
            
            db.session.add(document)
            generated_files.append({
                'name': certificate_data['recipient_name'],
                'download_url': url_for('download_document', document_uuid=document.uuid)
            })
        
        user.documents_created += len(generated_files)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Certificate(s) generated successfully!',
            'files': generated_files,
            'count': len(generated_files)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to generate certificate: {str(e)}'
        }), 500

@tools_bp.route('/templates/<document_type>')
@login_required
def get_templates(document_type):
    user = get_current_user()
    templates = Template.query.filter_by(document_type=document_type, is_active=True).all()
    
    available_templates = []
    for template in templates:
        template_data = template.to_dict()
        template_data['available'] = not template.is_premium or user.is_premium()
        available_templates.append(template_data)
    
    return jsonify({'templates': available_templates})