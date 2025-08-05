class Loan:
    def __init__(self, loan_id, amount, interest_rate, term):
        self.loan_id = loan_id
        self.amount = amount
        self.interest_rate = interest_rate
        self.term = term  # in months

    def calculate_monthly_payment(self):
        if self.interest_rate == 0:
            return self.amount / self.term
        monthly_rate = self.interest_rate / 100 / 12
        return (self.amount * monthly_rate) / (1 - (1 + monthly_rate) ** -self.term)

    def total_payment(self):
        return self.calculate_monthly_payment() * self.term

    def total_interest(self):
        return self.total_payment() - self.amount

    def __str__(self):
        return f"Loan(ID: {self.loan_id}, Amount: {self.amount}, Interest Rate: {self.interest_rate}, Term: {self.term})"