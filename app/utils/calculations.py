import math
from decimal import Decimal, ROUND_HALF_UP

def calculate_emi(principal, annual_rate, tenure_months):
    """
    Calculate EMI using reducing balance method.
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate (percentage)
        tenure_months: Loan tenure in months
    
    Returns:
        Dictionary with EMI details
    """
    try:
        # Convert to appropriate types
        principal = float(principal)
        annual_rate = float(annual_rate)
        tenure_months = int(tenure_months)
        
        if principal <= 0 or annual_rate < 0 or tenure_months <= 0:
            raise ValueError("Invalid input values")
        
        # Calculate monthly interest rate
        monthly_rate = annual_rate / 100 / 12
        
        # Calculate EMI using formula: P * r * (1+r)^n / ((1+r)^n - 1)
        if monthly_rate == 0:
            # For 0% interest
            emi = principal / tenure_months
        else:
            power_term = (1 + monthly_rate) ** tenure_months
            emi = principal * monthly_rate * power_term / (power_term - 1)
        
        # Round to 2 decimal places
        emi = round(emi, 2)
        total_amount = round(emi * tenure_months, 2)
        total_interest = round(total_amount - principal, 2)
        
        # Generate payment breakdown
        breakdown = generate_payment_breakdown(principal, monthly_rate, tenure_months, emi)
        
        return {
            'emi': emi,
            'total_amount': total_amount,
            'total_interest': total_interest,
            'monthly_rate': round(monthly_rate * 100, 4),
            'breakdown': breakdown
        }
    
    except Exception as e:
        raise ValueError(f"EMI calculation failed: {str(e)}")

def generate_payment_breakdown(principal, monthly_rate, tenure_months, emi):
    """Generate month-wise payment breakdown."""
    breakdown = []
    balance = principal
    
    for month in range(1, tenure_months + 1):
        interest_payment = balance * monthly_rate
        principal_payment = emi - interest_payment
        balance -= principal_payment
        
        # Ensure balance doesn't go negative due to rounding
        if balance < 0:
            principal_payment += balance
            balance = 0
        
        breakdown.append({
            'month': month,
            'emi': round(emi, 2),
            'principal': round(principal_payment, 2),
            'interest': round(interest_payment, 2),
            'balance': round(balance, 2)
        })
    
    return breakdown

def calculate_compound_interest(principal, annual_rate, time_years, compounding_frequency=12):
    """
    Calculate compound interest.
    
    Args:
        principal: Principal amount
        annual_rate: Annual interest rate (percentage)
        time_years: Time period in years
        compounding_frequency: Number of times interest is compounded per year
    
    Returns:
        Dictionary with compound interest details
    """
    try:
        principal = float(principal)
        annual_rate = float(annual_rate)
        time_years = float(time_years)
        compounding_frequency = int(compounding_frequency)
        
        if principal <= 0 or annual_rate < 0 or time_years <= 0:
            raise ValueError("Invalid input values")
        
        # A = P(1 + r/n)^(nt)
        rate_per_period = annual_rate / 100 / compounding_frequency
        total_periods = compounding_frequency * time_years
        
        amount = principal * ((1 + rate_per_period) ** total_periods)
        compound_interest = amount - principal
        
        return {
            'principal': round(principal, 2),
            'amount': round(amount, 2),
            'compound_interest': round(compound_interest, 2),
            'effective_annual_rate': round(((amount / principal) ** (1 / time_years) - 1) * 100, 2)
        }
    
    except Exception as e:
        raise ValueError(f"Compound interest calculation failed: {str(e)}")

def calculate_simple_interest(principal, annual_rate, time_years):
    """
    Calculate simple interest.
    
    Args:
        principal: Principal amount
        annual_rate: Annual interest rate (percentage)
        time_years: Time period in years
    
    Returns:
        Dictionary with simple interest details
    """
    try:
        principal = float(principal)
        annual_rate = float(annual_rate)
        time_years = float(time_years)
        
        if principal <= 0 or annual_rate < 0 or time_years <= 0:
            raise ValueError("Invalid input values")
        
        # SI = P * R * T / 100
        simple_interest = principal * annual_rate * time_years / 100
        amount = principal + simple_interest
        
        return {
            'principal': round(principal, 2),
            'simple_interest': round(simple_interest, 2),
            'amount': round(amount, 2)
        }
    
    except Exception as e:
        raise ValueError(f"Simple interest calculation failed: {str(e)}")

def calculate_gold_loan_amount(gold_weight_grams, purity_carats, gold_rate_per_gram, ltv_percentage=75):
    """
    Calculate gold loan eligible amount.
    
    Args:
        gold_weight_grams: Weight of gold in grams
        purity_carats: Purity of gold in carats (e.g., 22, 18)
        gold_rate_per_gram: Current gold rate per gram
        ltv_percentage: Loan to Value ratio percentage
    
    Returns:
        Dictionary with gold loan details
    """
    try:
        gold_weight = float(gold_weight_grams)
        purity = float(purity_carats)
        rate = float(gold_rate_per_gram)
        ltv = float(ltv_percentage)
        
        if gold_weight <= 0 or purity <= 0 or rate <= 0 or ltv <= 0:
            raise ValueError("Invalid input values")
        
        # Calculate purity factor (22 carat = 91.67%, 18 carat = 75%)
        purity_factor = purity / 24
        
        # Calculate gold value
        pure_gold_weight = gold_weight * purity_factor
        gold_value = pure_gold_weight * rate
        
        # Calculate eligible loan amount
        eligible_amount = gold_value * (ltv / 100)
        
        return {
            'gold_weight': round(gold_weight, 2),
            'pure_gold_weight': round(pure_gold_weight, 2),
            'purity_percentage': round(purity_factor * 100, 2),
            'gold_value': round(gold_value, 2),
            'ltv_percentage': ltv,
            'eligible_amount': round(eligible_amount, 2),
            'ltv_amount': round(gold_value * (ltv / 100), 2),
            'details': {
                'rate_per_gram': rate,
                'total_value': round(gold_value, 2),
                'max_loan_amount': round(eligible_amount, 2)
            }
        }
    
    except Exception as e:
        raise ValueError(f"Gold loan calculation failed: {str(e)}")

def calculate_reducing_balance_interest(principal, annual_rate, months_elapsed):
    """Calculate interest for reducing balance method."""
    try:
        principal = float(principal)
        annual_rate = float(annual_rate)
        months_elapsed = int(months_elapsed)
        
        monthly_rate = annual_rate / 100 / 12
        
        # Calculate interest for the period
        interest = principal * monthly_rate * months_elapsed
        
        return round(interest, 2)
    
    except Exception as e:
        raise ValueError(f"Interest calculation failed: {str(e)}")

def calculate_loan_maturity_amount(principal, annual_rate, tenure_months, interest_type='reducing'):
    """Calculate loan maturity amount based on interest type."""
    try:
        if interest_type == 'reducing':
            emi_calc = calculate_emi(principal, annual_rate, tenure_months)
            return emi_calc['total_amount']
        
        elif interest_type == 'simple':
            si_calc = calculate_simple_interest(principal, annual_rate, tenure_months / 12)
            return si_calc['amount']
        
        elif interest_type == 'compound':
            ci_calc = calculate_compound_interest(principal, annual_rate, tenure_months / 12)
            return ci_calc['amount']
        
        else:
            raise ValueError("Invalid interest type")
    
    except Exception as e:
        raise ValueError(f"Maturity calculation failed: {str(e)}")

def calculate_prepayment_savings(current_balance, remaining_months, monthly_emi, prepayment_amount, annual_rate):
    """Calculate savings from prepayment."""
    try:
        current_balance = float(current_balance)
        remaining_months = int(remaining_months)
        monthly_emi = float(monthly_emi)
        prepayment_amount = float(prepayment_amount)
        annual_rate = float(annual_rate)
        
        if prepayment_amount > current_balance:
            prepayment_amount = current_balance
        
        # Calculate remaining interest without prepayment
        original_total = monthly_emi * remaining_months
        original_interest = original_total - current_balance
        
        # Calculate new balance after prepayment
        new_balance = current_balance - prepayment_amount
        
        if new_balance <= 0:
            # Full prepayment
            return {
                'interest_saved': original_interest,
                'new_balance': 0,
                'new_emi': 0,
                'new_tenure': 0,
                'total_savings': original_interest
            }
        
        # Calculate new EMI or tenure (assuming tenure reduction)
        monthly_rate = annual_rate / 100 / 12
        
        if monthly_rate == 0:
            new_tenure = math.ceil(new_balance / monthly_emi)
            new_total_payment = monthly_emi * new_tenure
        else:
            # Calculate new tenure with same EMI
            new_tenure = math.ceil(
                math.log(1 + (new_balance * monthly_rate / monthly_emi)) / 
                math.log(1 + monthly_rate)
            )
            new_total_payment = monthly_emi * new_tenure
        
        new_interest = new_total_payment - new_balance
        interest_saved = original_interest - new_interest
        
        return {
            'interest_saved': round(interest_saved, 2),
            'new_balance': round(new_balance, 2),
            'new_emi': monthly_emi,
            'new_tenure': new_tenure,
            'total_savings': round(interest_saved, 2)
        }
    
    except Exception as e:
        raise ValueError(f"Prepayment calculation failed: {str(e)}")

def calculate_late_payment_penalty(emi_amount, days_late, penalty_rate_per_day=0.1):
    """Calculate late payment penalty."""
    try:
        emi_amount = float(emi_amount)
        days_late = int(days_late)
        penalty_rate = float(penalty_rate_per_day)
        
        if days_late <= 0:
            return 0
        
        penalty = emi_amount * (penalty_rate / 100) * days_late
        
        return round(penalty, 2)
    
    except Exception as e:
        raise ValueError(f"Penalty calculation failed: {str(e)}")

def round_currency(amount, decimals=2):
    """Round currency amount to specified decimal places."""
    try:
        decimal_amount = Decimal(str(amount))
        rounded = decimal_amount.quantize(
            Decimal('0.' + '0' * decimals), 
            rounding=ROUND_HALF_UP
        )
        return float(rounded)
    except:
        return round(float(amount), decimals)