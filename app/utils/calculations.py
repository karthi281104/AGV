def calculate_loan_interest(principal, rate, time):
    """Calculate the interest on a loan."""
    return principal * (rate / 100) * time

def calculate_monthly_payment(principal, rate, term):
    """Calculate the monthly payment for a loan."""
    monthly_rate = rate / 100 / 12
    number_of_payments = term * 12
    if rate == 0:
        return principal / number_of_payments
    return principal * (monthly_rate * (1 + monthly_rate) ** number_of_payments) / ((1 + monthly_rate) ** number_of_payments - 1)

def calculate_total_payment(monthly_payment, term):
    """Calculate the total payment over the term of the loan."""
    return monthly_payment * term * 12

def calculate_total_interest(total_payment, principal):
    """Calculate the total interest paid over the life of the loan."""
    return total_payment - principal