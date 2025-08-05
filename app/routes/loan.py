from flask import Blueprint, request, jsonify, render_template
from app.models.loan import Loan

loan_bp = Blueprint('loan', __name__)

@loan_bp.route('/loans', methods=['GET'])
def loan_list():
    # Logic to retrieve and display all loans
    loans = Loan.get_all_loans()  # Assuming a method to get all loans
    return render_template('loans/loan_list.html', loans=loans)

@loan_bp.route('/loans/<int:loan_id>', methods=['GET'])
def loan_detail(loan_id):
    # Logic to retrieve and display a specific loan
    loan = Loan.get_loan_by_id(loan_id)  # Assuming a method to get loan by ID
    if loan:
        return render_template('loans/loan_detail.html', loan=loan)
    return jsonify({'error': 'Loan not found'}), 404

@loan_bp.route('/loans/apply', methods=['POST'])
def apply_loan():
    # Logic to apply for a new loan
    data = request.json
    new_loan = Loan(
        amount=data['amount'],
        interest_rate=data['interest_rate'],
        term=data['term']
    )
    new_loan.save()  # Assuming a method to save the loan
    return jsonify({'message': 'Loan application submitted successfully'}), 201