from flask import Blueprint, render_template, request, jsonify
from app.models.loan import Loan
from app.models.customer import Customer
from app.utils.calculations import calculate_emi, calculate_gold_loan_amount

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Public homepage with company info and calculators"""
    return render_template('index.html')


@main_bp.route('/calculator/emi', methods=['POST'])
def emi_calculator():
    """EMI Calculator API for public use"""
    try:
        principal = float(request.json.get('principal'))
        rate = float(request.json.get('rate'))
        tenure = int(request.json.get('tenure'))

        emi = calculate_emi(principal, rate, tenure)
        total_amount = emi * tenure
        total_interest = total_amount - principal

        return jsonify({
            'emi': round(emi, 2),
            'total_amount': round(total_amount, 2),
            'total_interest': round(total_interest, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@main_bp.route('/calculator/gold-loan', methods=['POST'])
def gold_loan_calculator():
    """Gold Loan Calculator API for public use"""
    try:
        gold_weight = float(request.json.get('weight'))
        gold_purity = float(request.json.get('purity'))
        current_rate = float(request.json.get('current_rate'))
        ltv_ratio = float(request.json.get('ltv_ratio', 75))  # Default 75%

        max_loan_amount = calculate_gold_loan_amount(
            gold_weight, gold_purity, current_rate, ltv_ratio
        )

        return jsonify({
            'max_loan_amount': round(max_loan_amount, 2),
            'gold_value': round(gold_weight * gold_purity * current_rate / 100, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400