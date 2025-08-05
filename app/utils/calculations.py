import math
from decimal import Decimal


def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate EMI for a loan"""
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return principal / tenure_months

    emi = principal * (monthly_rate * (1 + monthly_rate) ** tenure_months) / ((1 + monthly_rate) ** tenure_months - 1)
    return emi


def calculate_gold_loan_amount(weight_grams, purity_percentage, rate_per_gram, ltv_ratio=75):
    """Calculate maximum loan amount for gold"""
    pure_gold_weight = weight_grams * purity_percentage / 100
    gold_value = pure_gold_weight * rate_per_gram
    max_loan = gold_value * ltv_ratio / 100
    return max_loan


def calculate_interest_accrued(principal, annual_rate, days):
    """Calculate interest accrued for given days"""
    daily_rate = annual_rate / 100 / 365
    interest = principal * daily_rate * days
    return interest


def generate_loan_id():
    """Generate unique loan ID"""
    import datetime
    import random
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    random_part = f"{random.randint(1000, 9999)}"
    return f"AGV{timestamp}{random_part}"


def generate_customer_id():
    """Generate unique customer ID"""
    import datetime
    import random
    timestamp = datetime.datetime.now().strftime("%Y%m")
    random_part = f"{random.randint(100, 999)}"
    return f"CUST{timestamp}{random_part}"


def generate_payment_id():
    """Generate unique payment ID"""
    import datetime
    import random
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    random_part = f"{random.randint(100, 999)}"
    return f"PAY{timestamp}{random_part}"