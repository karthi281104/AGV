# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .customer import Customer
from .loan import Loan
from .payment import Payment

__all__ = ['User', 'Customer', 'Loan', 'Payment']