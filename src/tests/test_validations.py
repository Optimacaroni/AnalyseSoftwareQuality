import unittest
from validation import (
    validate_first_name, validate_last_name, validate_birthday, validate_gender,
    validate_street, validate_house_number, validate_postal_code, validate_city,
    validate_email, validate_phone_number, validate_driving_license,
    validate_username, validate_password
)
import database

class TestValidations(unittest.TestCase):

    def test_names(self):
        self.assertTrue(validate_first_name("John"))
        self.assertTrue(validate_last_name("O'Connor"))
        self.assertFalse(validate_first_name("john1"))
        self.assertFalse(validate_last_name(""))

    def test_birthday_gender(self):
        self.assertTrue(validate_birthday("1990-12-31"))
        self.assertFalse(validate_birthday("31-12-1990"))
        self.assertTrue(validate_gender("Male"))
        self.assertFalse(validate_gender("Unknown"))

    def test_address(self):
        self.assertTrue(validate_street("Main Street"))
        self.assertTrue(validate_house_number("123"))
        self.assertTrue(validate_postal_code("1234AB"))
        self.assertFalse(validate_postal_code("1234 AB"))
        self.assertTrue(validate_city(database.Cities[0]))
        self.assertFalse(validate_city("Unknown City"))

    def test_contact_and_license(self):
        self.assertTrue(validate_email("john.doe@example.com"))
        self.assertTrue(validate_phone_number("12345678"))
        self.assertFalse(validate_phone_number("123456789"))
        self.assertTrue(validate_driving_license("AB1234567"))
        self.assertTrue(validate_driving_license("A12345678"))
        self.assertFalse(validate_driving_license("ABC123456"))

    def test_username_password_policy(self):
        self.assertTrue(validate_username("john_doe1"))
        self.assertFalse(validate_username("1john_doe"))   # must start with letter/_ 
        self.assertFalse(validate_username("short"))        # too short
        self.assertTrue(validate_password("StrongPassw0rd!"))
        self.assertFalse(validate_password("weakpass"))

if __name__ == '__main__':
    unittest.main()
