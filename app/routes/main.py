from flask import Blueprint, render_template, request, jsonify
from app.models.loan import Loan
from app.models.customer import Customer
from app.utils.calculations import calculate_emi, calculate_gold_loan_amount

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Homepage with loan calculators and company information."""
    # Get some basic statistics for homepage
    total_customers = Customer.query.filter_by(is_active=True).count()
    active_loans = Loan.query.filter_by(status='disbursed').count()
    
    stats = {
        'total_customers': total_customers,
        'active_loans': active_loans,
        'loan_types': ['Personal Loan', 'Gold Loan', 'Vehicle Loan', 'Home Loan']
    }
    
    return render_template('index.html', stats=stats)

@bp.route('/about')
def about():
    """About page with company information."""
    return render_template('about.html')

@bp.route('/services')
def services():
    """Services page showing available loan types."""
    loan_types = [
        {
            'name': 'Personal Loan',
            'description': 'Unsecured loans for personal needs',
            'interest_rate': '12-24%',
            'max_amount': '₹5,00,000',
            'tenure': '12-60 months'
        },
        {
            'name': 'Gold Loan',
            'description': 'Loans against gold jewelry',
            'interest_rate': '10-18%',
            'max_amount': '₹50,00,000',
            'tenure': '6-36 months'
        },
        {
            'name': 'Vehicle Loan',
            'description': 'Loans for two-wheelers and four-wheelers',
            'interest_rate': '8-15%',
            'max_amount': '₹20,00,000',
            'tenure': '12-84 months'
        },
        {
            'name': 'Home Loan',
            'description': 'Loans for purchasing or constructing homes',
            'interest_rate': '7-12%',
            'max_amount': '₹1,00,00,000',
            'tenure': '120-360 months'
        }
    ]
    return render_template('services.html', loan_types=loan_types)

@bp.route('/contact')
def contact():
    """Contact page with company details."""
    contact_info = {
        'address': 'AGV Finance and Loans, 123 Main Street, Financial District, City - 600001',
        'phone': '+91-9876543210',
        'email': 'info@agvfinance.com',
        'business_hours': 'Monday to Saturday: 9:00 AM - 6:00 PM'
    }
    return render_template('contact.html', contact_info=contact_info)

@bp.route('/calculator')
def calculator():
    """Loan calculator page."""
    return render_template('calculator.html')

@bp.route('/api/calculate-emi', methods=['POST'])
def api_calculate_emi():
    """API endpoint for EMI calculation."""
    try:
        data = request.get_json()
        principal = float(data.get('principal', 0))
        rate = float(data.get('rate', 0))
        tenure = int(data.get('tenure', 0))
        
        if principal <= 0 or rate <= 0 or tenure <= 0:
            return jsonify({'error': 'Invalid input values'}), 400
        
        emi_result = calculate_emi(principal, rate, tenure)
        
        return jsonify({
            'success': True,
            'emi': emi_result['emi'],
            'total_amount': emi_result['total_amount'],
            'total_interest': emi_result['total_interest'],
            'breakdown': emi_result['breakdown']
        })
    
    except (ValueError, KeyError) as e:
        return jsonify({'error': 'Invalid input data'}), 400
    except Exception as e:
        return jsonify({'error': 'Calculation failed'}), 500

@bp.route('/api/calculate-gold-loan', methods=['POST'])
def api_calculate_gold_loan():
    """API endpoint for gold loan calculation."""
    try:
        data = request.get_json()
        gold_weight = float(data.get('weight', 0))  # in grams
        gold_purity = float(data.get('purity', 22))  # in carats
        gold_rate = float(data.get('rate', 5000))  # per gram
        ltv_ratio = float(data.get('ltv', 75))  # loan to value percentage
        
        if gold_weight <= 0:
            return jsonify({'error': 'Invalid gold weight'}), 400
        
        loan_result = calculate_gold_loan_amount(gold_weight, gold_purity, gold_rate, ltv_ratio)
        
        return jsonify({
            'success': True,
            'eligible_amount': loan_result['eligible_amount'],
            'gold_value': loan_result['gold_value'],
            'ltv_amount': loan_result['ltv_amount'],
            'details': loan_result['details']
        })
    
    except (ValueError, KeyError) as e:
        return jsonify({'error': 'Invalid input data'}), 400
    except Exception as e:
        return jsonify({'error': 'Calculation failed'}), 500

@bp.route('/api/interest-rates')
def api_interest_rates():
    """API endpoint to get current interest rates."""
    rates = {
        'personal_loan': {'min': 12.0, 'max': 24.0},
        'gold_loan': {'min': 10.0, 'max': 18.0},
        'vehicle_loan': {'min': 8.0, 'max': 15.0},
        'home_loan': {'min': 7.0, 'max': 12.0}
    }
    return jsonify({'success': True, 'rates': rates})

@bp.route('/apply')
def apply():
    """Loan application landing page."""
    return render_template('apply.html')

# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500