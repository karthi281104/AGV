def format_currency(amount):
    """Formats a number as currency."""
    return "${:,.2f}".format(amount)

def calculate_percentage(part, whole):
    """Calculates the percentage of a part relative to a whole."""
    if whole == 0:
        return 0
    return (part / whole) * 100

def validate_email(email):
    """Validates the format of an email address."""
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def generate_unique_id(existing_ids):
    """Generates a unique ID not present in the existing IDs."""
    import uuid
    new_id = str(uuid.uuid4())
    while new_id in existing_ids:
        new_id = str(uuid.uuid4())
    return new_id

def sanitize_input(user_input):
    """Sanitizes user input to prevent injection attacks."""
    import html
    return html.escape(user_input)