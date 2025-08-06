# app/models/__init__.py

from .auth import User, UserSession, WebAuthnCredential
from .core import Customer, Loan, Payment, Document
from .dashboard import DashboardMetrics, RealtimeData, UserPreferences, AlertSettings, DashboardActivity

__all__ = [
    'User', 'UserSession', 'WebAuthnCredential',
    'Customer', 'Loan', 'Payment', 'Document',
    'DashboardMetrics', 'RealtimeData', 'UserPreferences', 'AlertSettings', 'DashboardActivity'
]