class Payment:
    def __init__(self, id, loan_id, amount, date):
        self.id = id
        self.loan_id = loan_id
        self.amount = amount
        self.date = date

    def process_payment(self):
        # Logic to process the payment
        pass

    def get_payment_details(self):
        return {
            "id": self.id,
            "loan_id": self.loan_id,
            "amount": self.amount,
            "date": self.date
        }