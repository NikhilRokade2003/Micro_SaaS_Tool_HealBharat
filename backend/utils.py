import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.pdfgen import canvas
from io import BytesIO
import json
from datetime import datetime

def generate_invoice_pdf(invoice_data, file_path):
    """Generate invoice PDF using ReportLab"""
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("INVOICE", title_style))
    
    # Company and Client Info
    info_data = [
        ['From:', 'To:'],
        [invoice_data['company_name'], invoice_data['client_name']],
        [invoice_data['company_address'], invoice_data['client_address']],
        [invoice_data['company_email'], invoice_data['client_email']],
        [invoice_data['company_phone'], '']
    ]
    
    info_table = Table(info_data, colWidths=[3*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Invoice Details
    details_data = [
        ['Invoice Number:', invoice_data['invoice_number']],
        ['Invoice Date:', invoice_data['invoice_date']],
        ['Due Date:', invoice_data['due_date']]
    ]
    
    details_table = Table(details_data, colWidths=[2*inch, 2*inch])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 30))
    
    # Items Table
    items_header = ['Description', 'Quantity', 'Rate', 'Amount']
    items_data = [items_header]
    
    subtotal = 0
    for item in invoice_data['items']:
        amount = float(item['quantity']) * float(item['rate'])
        subtotal += amount
        items_data.append([
            item['description'],
            str(item['quantity']),
            f"₹{float(item['rate']):.2f}",
            f"₹{amount:.2f}"
        ])
    
    # Calculate totals
    discount_amount = subtotal * (invoice_data['discount'] / 100)
    after_discount = subtotal - discount_amount
    tax_amount = after_discount * (invoice_data['tax_rate'] / 100)
    total = after_discount + tax_amount
    
    # Add totals to table
    items_data.extend([
        ['', '', 'Subtotal:', f"₹{subtotal:.2f}"],
        ['', '', f'Discount ({invoice_data["discount"]}%):', f"-₹{discount_amount:.2f}"],
        ['', '', f'Tax ({invoice_data["tax_rate"]}%):', f"₹{tax_amount:.2f}"],
        ['', '', 'Total:', f"₹{total:.2f}"]
    ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -4), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    story.append(items_table)
    
    # Notes
    if invoice_data.get('notes'):
        story.append(Spacer(1, 30))
        story.append(Paragraph("Notes:", styles['Heading3']))
        story.append(Paragraph(invoice_data['notes'], styles['Normal']))
    
    # Build PDF
    doc.build(story)

def generate_resume_pdf(resume_data, file_path):
    """Generate resume PDF using ReportLab"""
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Personal Information
    personal = resume_data['personal_info']
    story.append(Paragraph(personal['full_name'], styles['Title']))
    
    contact_info = f"{personal['email']} | {personal['phone']}"
    if personal.get('linkedin'):
        contact_info += f" | LinkedIn: {personal['linkedin']}"
    if personal.get('portfolio'):
        contact_info += f" | Portfolio: {personal['portfolio']}"
    
    story.append(Paragraph(contact_info, styles['Normal']))
    story.append(Paragraph(personal['address'], styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary
    if resume_data.get('summary'):
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles['Heading2']))
        story.append(Paragraph(resume_data['summary'], styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Experience
    if resume_data.get('experience'):
        story.append(Paragraph("WORK EXPERIENCE", styles['Heading2']))
        for exp in resume_data['experience']:
            story.append(Paragraph(f"<b>{exp['position']}</b> - {exp['company']}", styles['Heading3']))
            story.append(Paragraph(f"{exp['start_date']} - {exp['end_date']}", styles['Normal']))
            story.append(Paragraph(exp['description'], styles['Normal']))
            story.append(Spacer(1, 10))
    
    # Education
    if resume_data.get('education'):
        story.append(Paragraph("EDUCATION", styles['Heading2']))
        for edu in resume_data['education']:
            story.append(Paragraph(f"<b>{edu['degree']}</b> - {edu['institution']}", styles['Heading3']))
            story.append(Paragraph(f"{edu['year']} | GPA: {edu.get('gpa', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 10))
    
    # Skills
    if resume_data.get('skills'):
        story.append(Paragraph("SKILLS", styles['Heading2']))
        skills_text = ', '.join([skill['name'] for skill in resume_data['skills']])
        story.append(Paragraph(skills_text, styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Projects
    if resume_data.get('projects'):
        story.append(Paragraph("PROJECTS", styles['Heading2']))
        for project in resume_data['projects']:
            story.append(Paragraph(f"<b>{project['name']}</b>", styles['Heading3']))
            story.append(Paragraph(project['description'], styles['Normal']))
            if project.get('technologies'):
                story.append(Paragraph(f"Technologies: {project['technologies']}", styles['Normal']))
            story.append(Spacer(1, 10))
    
    # Certifications
    if resume_data.get('certifications'):
        story.append(Paragraph("CERTIFICATIONS", styles['Heading2']))
        for cert in resume_data['certifications']:
            story.append(Paragraph(f"• {cert['name']} - {cert['issuer']} ({cert['year']})", styles['Normal']))
    
    # Build PDF
    doc.build(story)

def generate_certificate_pdf(certificate_data, file_path):
    """Generate certificate PDF using ReportLab"""
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    
    # Draw border
    c.setLineWidth(3)
    c.setStrokeColor(colors.gold)
    c.rect(30, 30, width-60, height-60)
    
    c.setLineWidth(1)
    c.setStrokeColor(colors.black)
    c.rect(50, 50, width-100, height-100)
    
    # Title
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(colors.darkblue)
    title_text = "CERTIFICATE OF COMPLETION"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 36)
    c.drawString((width - title_width) / 2, height - 120, title_text)
    
    # Presented to
    c.setFont("Helvetica", 18)
    c.setFillColor(colors.black)
    presented_text = "This is to certify that"
    presented_width = c.stringWidth(presented_text, "Helvetica", 18)
    c.drawString((width - presented_width) / 2, height - 200, presented_text)
    
    # Recipient name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.darkred)
    name = certificate_data['recipient_name']
    name_width = c.stringWidth(name, "Helvetica-Bold", 28)
    c.drawString((width - name_width) / 2, height - 250, name)
    
    # Draw line under name
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(width/2 - name_width/2 - 20, height - 260, width/2 + name_width/2 + 20, height - 260)
    
    # Has successfully completed
    c.setFont("Helvetica", 16)
    c.setFillColor(colors.black)
    completed_text = "has successfully completed the course"
    completed_width = c.stringWidth(completed_text, "Helvetica", 16)
    c.drawString((width - completed_width) / 2, height - 320, completed_text)
    
    # Course name
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.darkgreen)
    course = certificate_data['course_name']
    course_width = c.stringWidth(course, "Helvetica-Bold", 20)
    c.drawString((width - course_width) / 2, height - 360, course)
    
    # Description
    if certificate_data.get('description'):
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)
        desc = certificate_data['description']
        desc_width = c.stringWidth(desc, "Helvetica", 12)
        c.drawString((width - desc_width) / 2, height - 400, desc)
    
    # Date and signature section
    c.setFont("Helvetica", 12)
    c.drawString(100, 150, f"Date: {certificate_data['completion_date']}")
    c.drawString(100, 120, f"Organization: {certificate_data['organization']}")
    
    # Instructor signature
    c.drawString(width - 250, 150, f"Instructor: {certificate_data['instructor_name']}")
    c.line(width - 250, 130, width - 80, 130)
    c.drawString(width - 200, 110, "Signature")
    
    c.save()

def generate_qr_code(content, file_path, size=300, format='png'):
    """Generate QR code using qrcode library"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    # Create QR code image
    if format.lower() == 'svg':
        from qrcode.image.svg import SvgPathImage
        img = qr.make_image(image_factory=SvgPathImage)
        img.save(file_path)
    else:
        img = qr.make_image(fill_color="black", back_color="white")
        # Resize image to specified size
        img = img.resize((size, size), Image.LANCZOS)
        img.save(file_path)

def allowed_file(filename, allowed_extensions):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def format_currency(amount, currency='INR'):
    """Format currency amount"""
    if currency == 'INR':
        return f"₹{amount:,.2f}"
    else:
        return f"${amount:,.2f}"

def generate_unique_filename(original_filename, prefix=''):
    """Generate unique filename with timestamp"""
    import uuid
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        return f"{prefix}{timestamp}_{unique_id}.{ext}"
    else:
        return f"{prefix}{timestamp}_{unique_id}"

def validate_file_size(file, max_size_mb=10):
    """Validate uploaded file size"""
    file.seek(0, 2)  # Seek to end of file
    size = file.tell()
    file.seek(0)  # Reset file pointer
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return size <= max_size_bytes

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s-.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-')

def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """Create thumbnail from image"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.LANCZOS)
            img.save(thumbnail_path)
        return True
    except Exception:
        return False

def get_file_size_human_readable(size_bytes):
    """Convert file size to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def extract_colors_from_image(image_path, num_colors=5):
    """Extract dominant colors from image"""
    try:
        from collections import Counter
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((100, 100))  # Resize for faster processing
        
        pixels = list(img.getdata())
        counter = Counter(pixels)
        most_common = counter.most_common(num_colors)
        
        colors = []
        for color, count in most_common:
            colors.append({
                'rgb': color,
                'hex': '#%02x%02x%02x' % color,
                'count': count
            })
        return colors
    except Exception:
        return []

def compress_pdf(input_path, output_path, quality=0.5):
    """Compress PDF file (basic implementation)"""
    # This is a placeholder - in production, you might use libraries like PyPDF2
    # For now, just copy the file
    import shutil
    shutil.copy2(input_path, output_path)
    return True

def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDF files"""
    try:
        from PyPDF2 import PdfWriter, PdfReader
        
        writer = PdfWriter()
        
        for pdf_path in pdf_paths:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
    except ImportError:
        # PyPDF2 not available, return False
        return False
    except Exception:
        return False

def generate_invoice_number():
    """Generate unique invoice number"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"INV-{timestamp}"

def calculate_tax(amount, tax_rate):
    """Calculate tax amount"""
    return amount * (tax_rate / 100)

def calculate_discount(amount, discount_rate):
    """Calculate discount amount"""
    return amount * (discount_rate / 100)

def format_date(date_str, input_format='%Y-%m-%d', output_format='%d %B %Y'):
    """Format date string"""
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_str

def send_email_notification(to_email, subject, body, attachment_path=None):
    """Send email notification (placeholder)"""
    # This is a placeholder function
    # In production, implement with Flask-Mail or similar
    print(f"Email sent to {to_email}: {subject}")
    return True

def backup_database():
    """Create database backup"""
    from datetime import datetime
    import shutil
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"database_backup_{timestamp}.db"
    
    try:
        shutil.copy2('database.db', f'backups/{backup_filename}')
        return backup_filename
    except Exception as e:
        print(f"Backup failed: {e}")
        return None

def cleanup_old_files(directory, days=30):
    """Clean up files older than specified days"""
    import os
    import time
    from datetime import datetime, timedelta
    
    cutoff = time.time() - (days * 24 * 60 * 60)
    cleaned_count = 0
    
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    cleaned_count += 1
        return cleaned_count
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return 0

def generate_qr_code(data, size=300, format='png', error_correction='M', 
                     foreground_color='#000000', background_color='#ffffff'):
    """Generate QR code with custom settings"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        if format.lower() == 'svg':
            import qrcode.image.svg
            img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        else:
            img = qr.make_image(fill_color=foreground_color, back_color=background_color)
            img = img.resize((size, size))
        
        return img
    except Exception as e:
        print(f"QR code generation failed: {e}")
        return None