# app/models/__init__.py

from .user import User
from .customer import Customer
from .loan import Loan
from .payment import Payment
from .dashboard import DashboardMetrics, RealtimeData, UserPreferences, AlertSettings, DashboardActivity

__all__ = [
    'User', 'Customer', 'Loan', 'Payment',
    'DashboardMetrics', 'RealtimeData', 'UserPreferences', 'AlertSettings', 'DashboardActivity'
]