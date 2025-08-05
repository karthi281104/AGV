from flask import Blueprint, request, jsonify, render_template
from app.models.payment import Payment
from app.models.loan import Loan

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/payments', methods=['GET'])
def payment_history():
    # Logic to retrieve payment history
    payments = Payment.get_all_payments()  # Assuming a method to get all payments
    return render_template('payments/payment_history.html', payments=payments)

@payment_bp.route('/payments/new', methods=['GET', 'POST'])
def make_payment():
    if request.method == 'POST':
        loan_id = request.form['loan_id']
        amount = request.form['amount']
        payment = Payment(loan_id=loan_id, amount=amount)
        payment.save()  # Assuming a method to save the payment
        return jsonify({'message': 'Payment successful!'}), 201
    return render_template('payments/payment_form.html')