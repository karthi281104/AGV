from flask import Flask

app = Flask(__name__)

from app.routes import main, auth, dashboard, customer, loan, payment

app.register_blueprint(main.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(customer.bp)
app.register_blueprint(loan.bp)
app.register_blueprint(payment.bp)