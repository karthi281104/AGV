# Import all route blueprints
from .main import bp as main_bp
from .auth import bp as auth_bp
from .dashboard import bp as dashboard_bp
from .customer import bp as customer_bp
from .loan import bp as loan_bp
from .payment import bp as payment_bp

__all__ = ['main_bp', 'auth_bp', 'dashboard_bp', 'customer_bp', 'loan_bp', 'payment_bp']