class User:
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

    def authenticate(self, password):
        return self.password == password

    def __repr__(self):
        return f"<User {self.username}>"