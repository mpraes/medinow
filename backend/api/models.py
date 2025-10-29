# This file will contain the data models for the application.

class User:
    def __init__(self, phone_number, name=None, email=None):
        self.phone_number = phone_number
        self.name = name
        self.email = email

class Appointment:
    def __init__(self, user, slot, status='pending'):
        self.user = user
        self.slot = slot
        self.status = status
