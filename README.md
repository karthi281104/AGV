# AGV Finance Loans

AGV Finance Loans is a web application designed to manage loans, customers, and payments efficiently. This application provides a user-friendly interface for users to apply for loans, manage customer data, and process payments.

## Features

- User authentication (login/logout)
- Dashboard for user-specific data and statistics
- Customer management (add, update, view)
- Loan management (apply for loans, view loan details)
- Payment processing (make payments, view payment history)

## Project Structure

```
agv-finance-loans/
├── app/
│   ├── models/          # Contains data models for User, Customer, Loan, and Payment
│   ├── routes/          # Contains route definitions for the application
│   ├── templates/       # Contains HTML templates for rendering views
│   ├── static/          # Contains static files (CSS, JS, uploads)
│   └── utils/           # Contains utility functions for authentication and calculations
├── migrations/          # Database migration files
├── config.py            # Configuration settings for the application
├── requirements.txt     # List of dependencies required for the project
├── run.py               # Entry point for running the application
└── README.md            # Documentation and instructions for the project
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/agv-finance-loans.git
   cd agv-finance-loans
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the environment variables in a `.env` file based on the provided `.env.example`.

## Usage

To run the application, execute the following command:
```
python run.py
```

Visit `http://127.0.0.1:5000` in your web browser to access the application.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.