#!/usr/bin/env python3
"""
AGV Finance and Loans Application
Run script for development and production deployment
"""

import os
from app import create_app, db, socketio
from app.models import User, Customer, Loan, Payment
from flask_migrate import upgrade

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Customer=Customer, Loan=Loan, Payment=Payment)

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Create database tables
    upgrade()
    
    # Create upload directories
    upload_dir = os.path.join(app.instance_path, 'uploads')
    documents_dir = os.path.join(upload_dir, 'documents')
    os.makedirs(documents_dir, exist_ok=True)

if __name__ == '__main__':
    # For development, use Flask dev server
    if app.config['DEBUG']:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        # For production, use gunicorn with socketio support
        socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))