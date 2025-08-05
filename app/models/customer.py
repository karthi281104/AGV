class Customer:
    def __init__(self, id, name, contact_info):
        self.id = id
        self.name = name
        self.contact_info = contact_info

    def update_contact_info(self, new_contact_info):
        self.contact_info = new_contact_info

    def get_customer_info(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact_info": self.contact_info
        }