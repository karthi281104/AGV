# AGV Finance and Loans

A comprehensive Flask-based financial management application for loan processing, customer management, and payment tracking with real-time dashboard analytics.

## 🚀 Features

### Core Functionality
- **Customer Management**: Complete customer lifecycle with biometric enrollment and document management
- **Loan Processing**: End-to-end loan application, approval, and disbursement workflow
- **Payment Processing**: Automated EMI calculations with principal/interest breakdown
- **Real-time Dashboard**: 6-metric dashboard with live updates via WebSocket
- **Auth0 Integration**: Secure authentication with WebAuthn biometric support
- **Financial Calculators**: Interactive EMI, eligibility, and prepayment calculators

### Advanced Features
- **Role-based Access Control**: Admin, Manager, and Employee roles with granular permissions
- **Document Management**: Secure file uploads with validation and organization
- **Automated Calculations**: EMI schedules, interest calculations, and loan analytics
- **Real-time Updates**: Live dashboard metrics using Flask-SocketIO
- **Responsive Design**: Bootstrap 5 with mobile-first approach
- **Production Ready**: Configured for deployment on Render, Heroku, or similar platforms

## 🛠 Technology Stack

### Backend
- **Flask 2.3.3**: Modern Python web framework
- **SQLAlchemy**: ORM with PostgreSQL support
- **Flask-Login**: Session management
- **Flask-Migrate**: Database migrations
- **Flask-SocketIO**: Real-time communications
- **Auth0**: Authentication and authorization
- **WebAuthn**: Biometric authentication support

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Interactive charts and analytics
- **Font Awesome**: Comprehensive icon library
- **Socket.IO**: Real-time client-side updates

### Database
- **PostgreSQL**: Primary database (SQLite for development)
- **Redis**: Session storage and real-time features

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+ (for production)
- Redis (for real-time features)
- Auth0 account for authentication

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/karthi281104/AGV.git
cd AGV/agv-finance-loans
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the `.env` file and configure your settings:
```bash
cp .env .env.local
```

Edit `.env.local` with your configuration:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost/agv_finance_loans
FLASK_CONFIG=development

# Auth0 Configuration
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_AUDIENCE=your-auth0-api-identifier

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 5. Database Setup
```bash
# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Or use the deploy command
flask deploy
```

### 6. Run the Application
```bash
# Development mode
python run.py

# Or using Flask CLI
flask run
```

The application will be available at `http://localhost:5000`

## 🔐 Auth0 Setup

### 1. Create Auth0 Application
1. Log in to your Auth0 dashboard
2. Create a new "Regular Web Application"
3. Configure the following settings:

**Allowed Callback URLs:**
```
http://localhost:5000/auth/callback,
https://your-domain.com/auth/callback
```

**Allowed Logout URLs:**
```
http://localhost:5000,
https://your-domain.com
```

### 2. Configure Auth0 Rules (Optional)
Add custom rules for role assignment and user metadata.

### 3. Enable WebAuthn (Optional)
Configure WebAuthn settings in your Auth0 dashboard for biometric authentication.

## 📊 Database Schema

### Key Models

#### User
- Auth0 integration with role-based access
- WebAuthn credentials storage
- Login tracking and audit trail

#### Customer
- Personal and financial information
- Biometric data and document storage
- KYC and verification status

#### Loan
- Complete loan lifecycle management
- EMI calculations and schedules
- Document requirements and uploads

#### Payment
- Principal/interest breakdown
- Multiple payment methods support
- Automatic loan balance updates

## 🎯 Usage Guide

### For Administrators
1. **User Management**: Assign roles and permissions
2. **Loan Approvals**: Review and approve loan applications
3. **System Configuration**: Manage application settings
4. **Reports and Analytics**: Access comprehensive reports

### For Managers
1. **Customer Oversight**: Review customer verifications
2. **Loan Management**: Process approvals and disbursements
3. **Team Coordination**: Manage employee activities
4. **Performance Monitoring**: Track team metrics

### For Employees
1. **Customer Registration**: Add new customers with KYC
2. **Loan Applications**: Create and manage loan applications
3. **Payment Processing**: Record and track payments
4. **Daily Operations**: Handle routine transactions

## 🚀 Deployment

### Render Deployment

1. **Create a new Web Service** on Render
2. **Connect your GitHub repository**
3. **Configure build settings**:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn -k eventlet -w 1 --bind 0.0.0.0:$PORT run:app
   ```
4. **Set environment variables** from your `.env` file
5. **Add PostgreSQL database** add-on
6. **Deploy the application**

### Heroku Deployment

1. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL and Redis add-ons**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   heroku addons:create heroku-redis:mini
   ```

3. **Configure environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set FLASK_CONFIG=production
   # Add other environment variables
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   heroku run flask db upgrade
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t agv-finance .
   ```

2. **Run with docker-compose**:
   ```bash
   docker-compose up -d
   ```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Test Coverage
The application includes comprehensive tests for:
- Model relationships and validations
- Route functionality and permissions
- Business logic and calculations
- API endpoints and responses

## 📈 Performance Optimization

### Database
- Indexed foreign keys and search fields
- Query optimization with eager loading
- Connection pooling for production

### Frontend
- Minified CSS and JavaScript
- CDN integration for Bootstrap and libraries
- Lazy loading for large datasets

### Caching
- Redis for session storage
- Query result caching
- Static file caching headers

## 🔒 Security Features

### Authentication & Authorization
- Auth0 OAuth 2.0 integration
- Role-based access control (RBAC)
- WebAuthn biometric authentication
- Session security and timeout

### Data Protection
- CSRF protection on all forms
- SQL injection prevention via ORM
- File upload validation and restrictions
- Sensitive data encryption

### Infrastructure Security
- HTTPS enforcement in production
- Security headers configuration
- Database connection encryption
- Environment variable protection

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Verify connection string
echo $DATABASE_URL
```

**Auth0 Authentication Issues**
- Verify callback URLs in Auth0 dashboard
- Check Auth0 credentials in environment variables
- Ensure domain configuration is correct

**Real-time Updates Not Working**
- Verify Redis connection
- Check SocketIO configuration
- Ensure firewall allows WebSocket connections

### Logs and Debugging
```bash
# Enable debug mode
export FLASK_DEBUG=1

# View application logs
tail -f logs/agv-finance.log

# Database query logging
export SQLALCHEMY_ECHO=True
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Support

### Documentation
- [API Documentation](docs/api.md)
- [User Manual](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)

### Contact
- **Email**: support@agvfinance.com
- **GitHub Issues**: [Create an issue](https://github.com/karthi281104/AGV/issues)
- **Documentation**: [Wiki](https://github.com/karthi281104/AGV/wiki)

## 🎉 Acknowledgments

- **Flask Community** for the excellent web framework
- **Bootstrap Team** for the responsive UI components
- **Auth0** for authentication services
- **Chart.js** for beautiful data visualizations
- **All Contributors** who helped build this application

---

**AGV Finance and Loans** - Empowering financial growth through technology.

Made with ❤️ by the AGV Team