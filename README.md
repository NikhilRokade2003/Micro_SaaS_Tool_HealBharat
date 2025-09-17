# Document Toolkit - Micro SaaS Platform

A comprehensive document generation platform that allows users to create professional invoices, resumes, certificates, and QR codes with a modern web interface.

## 🚀 Features

### User Features
- **Invoice Generator**: Create professional PDF invoices with tax calculations
- **Resume Builder**: Build resumes with multiple templates (PDF/DOCX)
- **Certificate Creator**: Generate certificates for events and achievements
- **QR Code Generator**: Create QR codes for URLs, WiFi, vCard, and more
- **User Dashboard**: Manage and download generated documents
- **Profile Management**: Update personal information and settings
- **Subscription System**: Free and Premium plans

### Admin Features
- **Admin Dashboard**: Analytics and system overview
- **User Management**: View, activate/deactivate, and manage users
- **Template Management**: Add, edit, and manage document templates
- **Reports & Analytics**: Export user data and usage statistics
- **Revenue Tracking**: Monitor subscription payments and revenue

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Document Generation**: ReportLab, qrcode, python-docx
- **Authentication**: Session-based with password hashing
- **Payments**: Razorpay (India) + Stripe (Global)
- **Deployment**: Render, Vercel, Heroku, Docker

## 📁 Project Structure

```
document-toolkit/
├── backend/
│   ├── templates/
│   │   ├── tools/          # Tool-specific templates
│   │   ├── admin/          # Admin panel templates
│   │   └── *.html          # Main templates
│   ├── static/
│   │   ├── css/            # Stylesheets
│   │   ├── js/             # JavaScript files
│   │   ├── uploads/        # User uploads
│   │   └── database.db     # SQLite database
│   ├── generated_files/    # Generated documents
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication routes
│   ├── tools.py            # Document generation routes
│   ├── admin.py            # Admin panel routes
│   ├── config.py           # Configuration settings
│   ├── utils.py            # Utility functions
│   └── requirements.txt    # Python dependencies
├── deployment/
│   ├── render.yaml         # Render deployment config
│   ├── vercel.json         # Vercel deployment config
│   └── Dockerfile          # Docker configuration
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Manual Installation and Setup

Follow these steps to set up and run the Document Toolkit project on any device:

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd document-toolkit
   ```

2. **Navigate to Backend Directory**
   ```bash
   cd backend
   ```

3. **Create a Virtual Environment**
   ```bash
   # On Windows
   python -m venv venv

   # On macOS/Linux
   python3 -m venv venv
   ```

4. **Activate the Virtual Environment**
   ```bash
   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

5. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Set Up Environment Variables (Optional)**
   Create a `.env` file in the `backend` directory with your custom settings:
   ```env
   SECRET_KEY=your-custom-secret-key
   DATABASE_URL=sqlite:///database.db
   FLASK_ENV=development
   ADMIN_EMAIL=admin@toolkit.com
   ADMIN_PASSWORD=admin123
   ```

7. **Initialize the Database**
   The database will be created automatically when you run the application for the first time. If you need to reset it:
   ```bash
   # Remove existing database (if any)
   rm -f static/database.db
   ```

8. **Run the Flask Application**
   ```bash
   python app.py
   ```

9. **Access the Application**
   - Open your web browser and go to: http://localhost:5000
   - Admin Panel: http://localhost:5000/admin/login

### Default Credentials
- **Admin Account**: admin@toolkit.com / admin123
- **User Account**: Sign up through the website to create a new user account

### Troubleshooting Setup Issues

- **Python Version Error**: Ensure you have Python 3.8+. Check with `python --version`
- **Virtual Environment Issues**: If activation fails, try `python -m venv venv --clear`
- **Dependency Installation Fails**: Update pip with `pip install --upgrade pip`
- **Port Already in Use**: Change the port in `app.py` or kill the process using port 5000
- **Database Errors**: Delete `static/database.db` and restart the application

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///database.db
JWT_SECRET_KEY=jwt-secret-change-this
FLASK_ENV=development

# Payment Integration (Demo Keys)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=rzp_test_your_key_secret
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key

# Admin Credentials
ADMIN_EMAIL=admin@toolkit.com
ADMIN_PASSWORD=admin123
```

### Payment Setup
1. **Razorpay (India)**:
   - Sign up at [Razorpay](https://razorpay.com)
   - Get API keys from dashboard
   - Update `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`

2. **Stripe (Global)**:
   - Sign up at [Stripe](https://stripe.com)
   - Get API keys from dashboard
   - Update `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY`

## 📱 Usage

### For Users
1. **Sign Up**: Create an account with email and password
2. **Choose Tool**: Select from Invoice, Resume, Certificate, or QR Code
3. **Fill Form**: Complete the required information
4. **Generate**: Click generate to create your document
5. **Download**: Download the generated PDF/image
6. **Manage**: View all documents in your dashboard

### For Admins
1. **Login**: Use admin credentials to access admin panel
2. **Dashboard**: View system analytics and user statistics
3. **User Management**: Manage user accounts and subscriptions
4. **Template Management**: Add and manage document templates
5. **Reports**: Export user data and generate reports

## 🚀 Deployment

### Render (Recommended)
1. Push code to GitHub
2. Connect Render to your repository
3. Use the provided `render.yaml` configuration
4. Set environment variables in Render dashboard
5. Deploy!

### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Configure environment variables
4. Deploy!

### Heroku
1. Install Heroku CLI
2. Create Heroku app: `heroku create your-app-name`
3. Set environment variables: `heroku config:set KEY=value`
4. Deploy: `git push heroku main`

### Docker
1. Build image: `docker build -t document-toolkit .`
2. Run container: `docker run -p 5000:5000 document-toolkit`

## 💰 Monetization

### Subscription Plans
- **Free Plan**: 5 documents/month, basic templates
- **Premium Plan**: Unlimited documents, premium templates, bulk generation

### Payment Processing
- **Razorpay**: For Indian customers
- **Stripe**: For global customers
- **Automatic Renewals**: Subscription management
- **Revenue Tracking**: Admin dashboard analytics

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Input validation and sanitization
- File upload security
- CSRF protection
- SQL injection prevention

## 📊 Analytics & Monitoring

- User registration and activity tracking
- Document generation statistics
- Revenue and subscription analytics
- System performance monitoring
- Error logging and reporting

## 🛠️ Development

### Adding New Tools
1. Create template in `templates/tools/`
2. Add route in `tools.py`
3. Update navigation in `base.html`
4. Add utility functions in `utils.py`

### Adding New Templates
1. Create template file in appropriate directory
2. Add template record to database
3. Update template selection in tool forms

### Customizing Styles
- Main stylesheet: `static/css/styles.css`
- Bootstrap 5 for responsive design
- Custom CSS variables for theming

## 🐛 Troubleshooting

### Common Issues

1. **Database Error**:
   ```bash
   rm static/database.db  # Delete and restart
   python app.py
   ```

2. **Module Not Found**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Port Already in Use**:
   ```bash
   # Change port in app.py
   app.run(debug=True, port=5001)
   ```

4. **Payment Integration Issues**:
   - Verify API keys are correct
   - Check webhook endpoints
   - Ensure HTTPS in production

## 📈 Performance Optimization

- Database indexing for faster queries
- File caching for generated documents
- Image optimization for uploads
- CDN integration for static assets
- Database connection pooling



