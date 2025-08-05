# Import all models to make them available when importing from app.models
from .user import User
from .customer import Customer
from .loan import Loan
from .payment import Payment

__all__ = ['User', 'Customer', 'Loan', 'Payment']