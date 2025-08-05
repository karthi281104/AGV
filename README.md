# AGV Finance and Loans - Flask Application

A comprehensive loan management system built with Flask, designed for finance companies to manage customers, loans, and payments efficiently.

## Features

### 🏦 Core Banking Features
- **Customer Management**: Complete customer profiles with biometric support
- **Loan Processing**: Multi-type loan support (Personal, Gold, Vehicle, Home)
- **Payment Tracking**: Comprehensive payment history and EMI management
- **Real-time Dashboard**: 6-block metrics dashboard with live updates
- **Document Management**: Secure file upload and storage

### 🔐 Security & Authentication
- **Auth0 Integration**: Secure authentication with WebAuthn support
- **Role-based Access**: Admin, Manager, and Employee roles
- **CSRF Protection**: Built-in security against cross-site request forgery
- **Input Validation**: Comprehensive form validation and sanitization

### 📊 Analytics & Reporting
- **Real-time Metrics**: Live dashboard with Socket.IO
- **Financial Reports**: Daily, monthly, and custom date range reports
- **Loan Analytics**: Distribution charts and payment trends
- **Export Capabilities**: CSV exports for data analysis

### 💻 User Interface
- **Responsive Design**: Bootstrap 5 based responsive UI
- **Interactive Calculators**: EMI and Gold loan calculators
- **Progressive Web App**: Mobile-friendly interface
- **Real-time Updates**: Live notifications and metrics updates

## Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLAlchemy with PostgreSQL
- **Authentication**: Auth0 + Flask-Login
- **Real-time**: Flask-SocketIO
- **Migrations**: Flask-Migrate

### Frontend
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Bootstrap Icons 1.10.0
- **JavaScript**: Vanilla JS with Socket.IO
- **Charts**: Chart.js (optional)

### Security
- **CSRF**: Flask-WTF
- **Authentication**: Authlib
- **Encryption**: Cryptography
- **JWT**: PyJWT

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js (for npm packages, optional)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/karthi281104/AGV.git
   cd AGV
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:5000`

## Quick Demo

To test the application quickly:

1. Start the application: `python run.py`
2. Visit `http://localhost:5000`
3. Click "Login" (Auth0 not configured, so use development login)
4. Enter any email to create a development account
5. Explore the dashboard and features

## Project Structure

```
agv-finance-loans/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/                  # Database models
│   ├── routes/                  # Route blueprints
│   ├── templates/               # Jinja2 templates
│   ├── static/                  # Static files
│   └── utils/                   # Utility functions
├── migrations/                  # Database migrations
├── config.py                   # Configuration classes
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point
└── README.md                   # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.

---

**AGV Finance and Loans** - Making financial services accessible and efficient.
