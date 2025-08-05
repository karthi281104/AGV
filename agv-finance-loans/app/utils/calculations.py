"""
Financial calculations utilities for AGV Finance and Loans
EMI calculations, interest calculations, and financial analysis
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

class LoanCalculator:
    """Comprehensive loan calculation utilities"""
    
    @staticmethod
    def calculate_emi(principal, annual_rate, months):
        """
        Calculate EMI using the standard formula
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        """
        try:
            principal = Decimal(str(principal))
            annual_rate = Decimal(str(annual_rate))
            months = int(months)
            
            if annual_rate == 0:
                return principal / months
            
            monthly_rate = annual_rate / 100 / 12
            
            # Calculate (1+r)^n
            factor = (1 + monthly_rate) ** months
            
            # Calculate EMI
            emi = principal * monthly_rate * factor / (factor - 1)
            
            return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except Exception as e:
            raise ValueError(f"Error calculating EMI: {e}")
    
    @staticmethod
    def calculate_total_interest(principal, annual_rate, months):
        """Calculate total interest payable"""
        emi = LoanCalculator.calculate_emi(principal, annual_rate, months)
        total_amount = emi * months
        return total_amount - Decimal(str(principal))
    
    @staticmethod
    def calculate_total_amount(principal, annual_rate, months):
        """Calculate total amount payable"""
        emi = LoanCalculator.calculate_emi(principal, annual_rate, months)
        return emi * months
    
    @staticmethod
    def generate_amortization_schedule(principal, annual_rate, months, start_date=None):
        """Generate complete amortization schedule"""
        if start_date is None:
            start_date = date.today() + timedelta(days=30)
        
        emi = LoanCalculator.calculate_emi(principal, annual_rate, months)
        monthly_rate = Decimal(str(annual_rate)) / 100 / 12
        
        schedule = []
        outstanding = Decimal(str(principal))
        
        for month in range(1, months + 1):
            interest_payment = outstanding * monthly_rate
            principal_payment = emi - interest_payment
            outstanding -= principal_payment
            
            # Ensure outstanding doesn't go negative due to rounding
            if outstanding < 0:
                principal_payment += outstanding
                outstanding = Decimal('0')
            
            payment_date = start_date + relativedelta(months=month-1)
            
            schedule.append({
                'month': month,
                'payment_date': payment_date,
                'emi_amount': float(emi),
                'principal_payment': float(principal_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'interest_payment': float(interest_payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'outstanding_balance': float(outstanding.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            })
        
        return schedule
    
    @staticmethod
    def calculate_prepayment_savings(principal, annual_rate, months, prepayment_amount, prepayment_month):
        """Calculate savings from prepayment"""
        original_schedule = LoanCalculator.generate_amortization_schedule(principal, annual_rate, months)
        
        # Find outstanding after prepayment month
        if prepayment_month > len(original_schedule):
            return None
        
        outstanding_before = Decimal(str(original_schedule[prepayment_month - 1]['outstanding_balance']))
        outstanding_after = outstanding_before - Decimal(str(prepayment_amount))
        
        if outstanding_after <= 0:
            # Full prepayment
            remaining_months = months - prepayment_month
            remaining_emis = remaining_months * Decimal(str(original_schedule[0]['emi_amount']))
            return {
                'savings': float(remaining_emis),
                'months_saved': remaining_months,
                'new_tenure': prepayment_month
            }
        
        # Partial prepayment - calculate new EMI
        remaining_months = months - prepayment_month
        new_emi = LoanCalculator.calculate_emi(outstanding_after, annual_rate, remaining_months)
        
        original_remaining = sum(
            original_schedule[i]['emi_amount'] 
            for i in range(prepayment_month, months)
        )
        
        new_remaining = float(new_emi * remaining_months)
        
        return {
            'savings': original_remaining - new_remaining,
            'new_emi': float(new_emi),
            'months_saved': 0,
            'new_tenure': months
        }

class InterestCalculator:
    """Interest calculation utilities"""
    
    @staticmethod
    def calculate_simple_interest(principal, rate, time_years):
        """Calculate simple interest"""
        return Decimal(str(principal)) * Decimal(str(rate)) * Decimal(str(time_years)) / 100
    
    @staticmethod
    def calculate_compound_interest(principal, rate, time_years, compounding_frequency=12):
        """Calculate compound interest"""
        principal = Decimal(str(principal))
        rate = Decimal(str(rate)) / 100
        time = Decimal(str(time_years))
        frequency = Decimal(str(compounding_frequency))
        
        amount = principal * (1 + rate / frequency) ** (frequency * time)
        return amount - principal
    
    @staticmethod
    def calculate_daily_interest(principal, annual_rate):
        """Calculate daily interest amount"""
        return Decimal(str(principal)) * Decimal(str(annual_rate)) / 100 / 365

class LoanEligibilityCalculator:
    """Calculate loan eligibility based on income and other factors"""
    
    @staticmethod
    def calculate_max_loan_amount(monthly_income, existing_emi, interest_rate, tenure_months, foir_ratio=0.5):
        """
        Calculate maximum loan amount based on income
        FOIR = Fixed Obligations to Income Ratio (typically 40-60%)
        """
        available_income = Decimal(str(monthly_income)) * Decimal(str(foir_ratio)) - Decimal(str(existing_emi))
        
        if available_income <= 0:
            return 0
        
        # Calculate principal that gives EMI equal to available income
        monthly_rate = Decimal(str(interest_rate)) / 100 / 12
        
        if monthly_rate == 0:
            return float(available_income * tenure_months)
        
        factor = (1 + monthly_rate) ** tenure_months
        max_principal = available_income * (factor - 1) / (monthly_rate * factor)
        
        return float(max_principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    @staticmethod
    def calculate_debt_to_income_ratio(monthly_income, total_monthly_obligations):
        """Calculate debt-to-income ratio"""
        if monthly_income == 0:
            return 0
        return (Decimal(str(total_monthly_obligations)) / Decimal(str(monthly_income))) * 100
    
    @staticmethod
    def calculate_loan_to_value_ratio(loan_amount, asset_value):
        """Calculate loan-to-value ratio"""
        if asset_value == 0:
            return 0
        return (Decimal(str(loan_amount)) / Decimal(str(asset_value))) * 100

class PaymentCalculator:
    """Payment and penalty calculations"""
    
    @staticmethod
    def calculate_late_fee(emi_amount, days_late, late_fee_rate=0.02):
        """Calculate late fee for overdue payments"""
        if days_late <= 0:
            return Decimal('0')
        
        # Late fee as percentage of EMI amount per month
        monthly_late_fee = Decimal(str(emi_amount)) * Decimal(str(late_fee_rate))
        daily_late_fee = monthly_late_fee / 30
        
        return daily_late_fee * days_late
    
    @staticmethod
    def calculate_bounce_charges(emi_amount, base_charge=500):
        """Calculate bounce charges for failed payments"""
        return Decimal(str(base_charge))
    
    @staticmethod
    def calculate_foreclosure_charges(outstanding_amount, foreclosure_rate=0.04):
        """Calculate foreclosure charges"""
        return Decimal(str(outstanding_amount)) * Decimal(str(foreclosure_rate))

class FinancialAnalyzer:
    """Financial analysis and ratios"""
    
    @staticmethod
    def calculate_irr(cash_flows):
        """Calculate Internal Rate of Return"""
        # Simplified IRR calculation using Newton-Raphson method
        def npv(rate, flows):
            return sum(cf / (1 + rate) ** i for i, cf in enumerate(flows))
        
        def npv_derivative(rate, flows):
            return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(flows))
        
        rate = 0.1  # Initial guess
        for _ in range(100):  # Max iterations
            npv_val = npv(rate, cash_flows)
            if abs(npv_val) < 1e-6:
                return rate
            
            npv_deriv = npv_derivative(rate, cash_flows)
            if npv_deriv == 0:
                break
            
            rate = rate - npv_val / npv_deriv
        
        return rate
    
    @staticmethod
    def calculate_portfolio_metrics(loans):
        """Calculate portfolio-level metrics"""
        if not loans:
            return {}
        
        total_principal = sum(float(loan.principal_amount) for loan in loans)
        total_outstanding = sum(float(loan.outstanding_balance) for loan in loans)
        total_disbursed = sum(float(loan.disbursed_amount) for loan in loans)
        
        active_loans = [loan for loan in loans if loan.status == 'active']
        overdue_loans = [loan for loan in active_loans if loan.is_overdue()]
        
        return {
            'total_loans': len(loans),
            'active_loans': len(active_loans),
            'total_principal': total_principal,
            'total_outstanding': total_outstanding,
            'total_disbursed': total_disbursed,
            'collection_efficiency': (total_disbursed - total_outstanding) / total_disbursed * 100 if total_disbursed > 0 else 0,
            'overdue_loans': len(overdue_loans),
            'overdue_percentage': len(overdue_loans) / len(active_loans) * 100 if active_loans else 0,
            'average_loan_size': total_principal / len(loans) if loans else 0
        }