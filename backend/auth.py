from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # At least 6 characters
    return len(password) >= 6

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    # Handle POST request
    data = request.get_json() if request.is_json else request.form
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    
    # Validation
    errors = []
    
    if not email or not validate_email(email):
        errors.append('Please enter a valid email address')
    
    if not password or not validate_password(password):
        errors.append('Password must be at least 6 characters long')
    
    if not full_name or len(full_name) < 2:
        errors.append('Please enter your full name')
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        errors.append('An account with this email already exists')
    
    if errors:
        if request.is_json:
            return jsonify({'success': False, 'errors': errors}), 400
        else:
            for error in errors:
                flash(error, 'danger')
            return render_template('signup.html', 
                                 email=email, 
                                 full_name=full_name)
    
    try:
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            subscription_plan='free'
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Auto login after signup
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name

        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Account created successfully!',
                'redirect': url_for('dashboard')
            })
        else:
            flash('Account created successfully! Welcome to Document Toolkit.', 'success')
            return redirect(url_for('profile'))

    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'errors': ['Registration failed. Please try again.']}), 500
        else:
            flash('Registration failed. Please try again.', 'danger')
            return render_template('signup.html',
                                 email=email,
                                 full_name=full_name)

@auth_bp.route('/check-auth')
def check_auth():
    """API endpoint to check if user is authenticated"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.is_active:
            return jsonify({
                'authenticated': True,
                'user': user.to_dict()
            })
    
    return jsonify({'authenticated': False}), 401

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    
    # For demo purposes, just show a message
    # In production, implement email-based password reset
    flash('Password reset functionality will be implemented with email service.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST request
    data = request.get_json() if request.is_json else request.form
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    # Validation
    if not email or not password:
        error_msg = 'Please enter both email and password'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 400
        else:
            flash(error_msg, 'danger')
            return render_template('login.html', email=email)
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        error_msg = 'Invalid email or password'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 401
        else:
            flash(error_msg, 'danger')
            return render_template('login.html', email=email)
    
    if not user.is_active:
        error_msg = 'Your account has been deactivated. Please contact support.'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 401
        else:
            flash(error_msg, 'warning')
            return render_template('login.html', email=email)
    
    try:
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name
        
        if remember_me:
            session.permanent = True
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': 'Login successful!',
                'redirect': url_for('dashboard'),
                'user': user.to_dict()
            })
        else:
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        db.session.rollback()
        error_msg = 'Login failed. Please try again.'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            flash(error_msg, 'danger')
            return render_template('login.html', email=email)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        if request.is_json:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        return redirect(url_for('auth.login'))
    
    data = request.get_json() if request.is_json else request.form
    
    full_name = data.get('full_name', '').strip()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    errors = []
    
    if not full_name or len(full_name) < 2:
        errors.append('Please enter your full name')
    
    # If changing password, validate current password
    if new_password:
        if not current_password:
            errors.append('Please enter your current password')
        elif not user.check_password(current_password):
            errors.append('Current password is incorrect')
        elif not validate_password(new_password):
            errors.append('New password must be at least 6 characters long')
    
    if errors:
        if request.is_json:
            return jsonify({'success': False, 'errors': errors}), 400
        else:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('profile'))
    
    try:
        # Update user information
        user.full_name = full_name
        session['user_name'] = full_name
        
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Profile updated successfully!'})
        else:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': 'Update failed. Please try again.'}), 500
        else:
            flash('Update failed. Please try again.', 'danger')
            return redirect(url_for('profile'))