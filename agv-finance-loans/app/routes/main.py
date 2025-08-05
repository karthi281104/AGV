"""
Main routes for AGV Finance and Loans
Public pages including homepage and loan calculators
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.utils.calculations import LoanCalculator, LoanEligibilityCalculator
from app.models.loan import Loan
from app.models.customer import Customer
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Homepage with loan calculators and general information"""
    # Get some basic statistics for display
    try:
        total_customers = Customer.query.count()
        total_loans = Loan.query.count()
        active_loans = Loan.query.filter_by(status='active').count()
    except Exception:
        # Database tables might not exist yet
        total_customers = 0
        total_loans = 0
        active_loans = 0
    
    stats = {
        'total_customers': total_customers,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'disbursed_amount': 0  # Will be calculated in template or separate function
    }
    
    return render_template('index.html', stats=stats)

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/services')
def services():
    """Services page"""
    return render_template('services.html')

@bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@bp.route('/loan-calculator')
def loan_calculator():
    """Interactive loan calculator page"""
    return render_template('calculators/loan_calculator.html')

@bp.route('/eligibility-calculator')
def eligibility_calculator():
    """Loan eligibility calculator page"""
    return render_template('calculators/eligibility_calculator.html')

@bp.route('/api/calculate-emi', methods=['POST'])
def calculate_emi():
    """API endpoint to calculate EMI"""
    try:
        data = request.get_json()
        
        principal = float(data.get('principal', 0))
        interest_rate = float(data.get('interest_rate', 0))
        tenure_months = int(data.get('tenure_months', 0))
        
        if principal <= 0 or interest_rate < 0 or tenure_months <= 0:
            return jsonify({'error': 'Invalid input parameters'}), 400
        
        emi = LoanCalculator.calculate_emi(principal, interest_rate, tenure_months)
        total_amount = LoanCalculator.calculate_total_amount(principal, interest_rate, tenure_months)
        total_interest = LoanCalculator.calculate_total_interest(principal, interest_rate, tenure_months)
        
        return jsonify({
            'emi': float(emi),
            'total_amount': float(total_amount),
            'total_interest': float(total_interest),
            'principal': principal,
            'interest_rate': interest_rate,
            'tenure_months': tenure_months
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/calculate-eligibility', methods=['POST'])
def calculate_eligibility():
    """API endpoint to calculate loan eligibility"""
    try:
        data = request.get_json()
        
        monthly_income = float(data.get('monthly_income', 0))
        existing_emi = float(data.get('existing_emi', 0))
        interest_rate = float(data.get('interest_rate', 10))
        tenure_months = int(data.get('tenure_months', 240))
        foir_ratio = float(data.get('foir_ratio', 0.5))
        
        if monthly_income <= 0:
            return jsonify({'error': 'Monthly income must be positive'}), 400
        
        max_loan_amount = LoanEligibilityCalculator.calculate_max_loan_amount(
            monthly_income, existing_emi, interest_rate, tenure_months, foir_ratio
        )
        
        if max_loan_amount > 0:
            max_emi = LoanCalculator.calculate_emi(max_loan_amount, interest_rate, tenure_months)
            debt_ratio = LoanEligibilityCalculator.calculate_debt_to_income_ratio(
                monthly_income, existing_emi + float(max_emi)
            )
        else:
            max_emi = 0
            debt_ratio = LoanEligibilityCalculator.calculate_debt_to_income_ratio(
                monthly_income, existing_emi
            )
        
        return jsonify({
            'max_loan_amount': max_loan_amount,
            'max_emi': float(max_emi),
            'available_income': (monthly_income * foir_ratio) - existing_emi,
            'debt_to_income_ratio': float(debt_ratio),
            'monthly_income': monthly_income,
            'existing_emi': existing_emi,
            'recommended_emi': float(max_emi)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/amortization-schedule', methods=['POST'])
def amortization_schedule():
    """API endpoint to generate amortization schedule"""
    try:
        data = request.get_json()
        
        principal = float(data.get('principal', 0))
        interest_rate = float(data.get('interest_rate', 0))
        tenure_months = int(data.get('tenure_months', 0))
        
        if principal <= 0 or interest_rate < 0 or tenure_months <= 0:
            return jsonify({'error': 'Invalid input parameters'}), 400
        
        # Limit schedule to reasonable size for web display
        if tenure_months > 360:  # 30 years max
            return jsonify({'error': 'Tenure too long for schedule generation'}), 400
        
        schedule = LoanCalculator.generate_amortization_schedule(
            principal, interest_rate, tenure_months
        )
        
        return jsonify({
            'schedule': schedule,
            'total_months': len(schedule),
            'total_amount': sum(item['emi_amount'] for item in schedule),
            'total_interest': sum(item['interest_payment'] for item in schedule)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prepayment-analysis', methods=['POST'])
def prepayment_analysis():
    """API endpoint to analyze prepayment benefits"""
    try:
        data = request.get_json()
        
        principal = float(data.get('principal', 0))
        interest_rate = float(data.get('interest_rate', 0))
        tenure_months = int(data.get('tenure_months', 0))
        prepayment_amount = float(data.get('prepayment_amount', 0))
        prepayment_month = int(data.get('prepayment_month', 12))
        
        if principal <= 0 or interest_rate < 0 or tenure_months <= 0:
            return jsonify({'error': 'Invalid input parameters'}), 400
        
        if prepayment_amount <= 0:
            return jsonify({'error': 'Prepayment amount must be positive'}), 400
        
        if prepayment_month <= 0 or prepayment_month >= tenure_months:
            return jsonify({'error': 'Invalid prepayment month'}), 400
        
        savings = LoanCalculator.calculate_prepayment_savings(
            principal, interest_rate, tenure_months, prepayment_amount, prepayment_month
        )
        
        if not savings:
            return jsonify({'error': 'Unable to calculate prepayment savings'}), 400
        
        return jsonify(savings)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/privacy-policy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('legal/privacy_policy.html')

@bp.route('/terms-of-service')
def terms_of_service():
    """Terms of service page"""
    return render_template('legal/terms_of_service.html')

@bp.route('/faq')
def faq():
    """Frequently asked questions page"""
    return render_template('support/faq.html')

@bp.route('/help')
def help():
    """Help and documentation page"""
    return render_template('support/help.html')

@bp.route('/api/search', methods=['GET'])
def search():
    """Global search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Search query too short'}), 400
        
        results = {
            'customers': [],
            'loans': [],
            'query': query
        }
        
        if search_type in ['all', 'customers']:
            # Search customers (limited results for performance)
            customers = Customer.query.filter(
                db.or_(
                    Customer.first_name.ilike(f'%{query}%'),
                    Customer.last_name.ilike(f'%{query}%'),
                    Customer.email.ilike(f'%{query}%'),
                    Customer.phone_primary.ilike(f'%{query}%'),
                    Customer.id_number.ilike(f'%{query}%')
                )
            ).limit(10).all()
            
            results['customers'] = [
                {
                    'id': customer.id,
                    'name': customer.full_name,
                    'email': customer.email,
                    'phone': customer.phone_primary,
                    'status': customer.status
                }
                for customer in customers
            ]
        
        if search_type in ['all', 'loans']:
            # Search loans
            loans = Loan.query.filter(
                db.or_(
                    Loan.loan_number.ilike(f'%{query}%'),
                    Loan.loan_type.ilike(f'%{query}%')
                )
            ).limit(10).all()
            
            results['loans'] = [
                {
                    'id': loan.id,
                    'loan_number': loan.loan_number,
                    'loan_type': loan.loan_type,
                    'customer_name': loan.customer.full_name,
                    'amount': float(loan.principal_amount),
                    'status': loan.status
                }
                for loan in loans
            ]
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers for main blueprint
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500