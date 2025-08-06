from flask import Blueprint, request, jsonify
from app.models.core import Customer

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers', methods=['GET'])
def get_customers():
    # Logic to retrieve all customers
    customers = Customer.get_all()
    return jsonify(customers), 200

@customer_bp.route('/customers', methods=['POST'])
def add_customer():
    # Logic to add a new customer
    data = request.json
    new_customer = Customer(name=data['name'], contact_info=data['contact_info'])
    new_customer.save()
    return jsonify(new_customer), 201

@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    # Logic to retrieve a specific customer by ID
    customer = Customer.get_by_id(customer_id)
    if customer:
        return jsonify(customer), 200
    return jsonify({'error': 'Customer not found'}), 404

@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    # Logic to update an existing customer
    data = request.json
    customer = Customer.get_by_id(customer_id)
    if customer:
        customer.name = data['name']
        customer.contact_info = data['contact_info']
        customer.save()
        return jsonify(customer), 200
    return jsonify({'error': 'Customer not found'}), 404

@customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    # Logic to delete a customer
    customer = Customer.get_by_id(customer_id)
    if customer:
        customer.delete()
        return jsonify({'message': 'Customer deleted'}), 204
    return jsonify({'error': 'Customer not found'}), 404