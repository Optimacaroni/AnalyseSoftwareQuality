import re
import datetime
import database

# Traveller/user validations and new password policy

def validate_first_name(first_name):
    # Letters, apostrophes, hyphens; 1-30 chars
    pattern = r"^[A-Za-z][A-Za-z'\-]{0,29}$"
    return bool(re.match(pattern, first_name))

def validate_last_name(last_name):
    # Letters, spaces, apostrophes, hyphens; 1-40 chars; no double spaces
    pattern = r"^[A-Za-z][A-Za-z'\-]*(?: [A-Za-z'\-]+)*$"
    return bool(re.match(pattern, last_name)) and len(last_name) <= 40

def validate_birthday(birthday):
    # ISO 8601: YYYY-MM-DD
    try:
        datetime.datetime.strptime(birthday, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_gender(gender):
    return gender in ("Male", "Female")

def validate_street(street):
    # Letters, spaces, hyphens; up to 50 chars
    pattern = r"^[A-Za-z]+(?:[ -][A-Za-z]+)*$"
    return bool(re.match(pattern, street)) and len(street) <= 50

def validate_house_number(house_number):
    try:
        n = int(house_number)
        return 0 < n <= 10000
    except ValueError:
        return False

def validate_postal_code(postal_code):
    # Dutch: DDDDXX, no space
    pattern = r"^[1-9][0-9]{3}[A-Z]{2}$"
    return bool(re.match(pattern, postal_code))

def validate_city(city):
    return city in database.Cities

def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+\-']+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email)) and len(email) <= 50

def validate_phone_number(phone_number):
    # Only 8 digits (user enters DDDDDDDD; system stores +31-6-DDDDDDDD)
    return bool(re.match(r"^[0-9]{8}$", phone_number))

def validate_driving_license(lic):
    # XXDDDDDDD or XDDDDDDDD
    return bool(re.match(r"^([A-Z]{2}\d{7}|[A-Z]{1}\d{8})$", lic))

def validate_username(username):
    # Case-insensitive: enforce allowed chars and 8-10 len; start with letter or underscore
    # Allowed: letters, digits, underscore, apostrophe, period
    # We normalize elsewhere to lowercase for uniqueness checks
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_'.]{7,9}$", username))

def validate_password(password):
    # 12-30 chars; at least one lowercase, uppercase, digit, and special char
    special = r"~!@#$%&_\-+=`|\()\{\}\[\]:;'<>,\.?/"
    pattern = rf"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[{re.escape(special)}]).{{12,30}}$"
    return bool(re.match(pattern, password))

# Deprecated (not used anymore, kept for compatibility in some menus/tests)
def validate_age(age):
    try:
        age = int(age)
    except ValueError:
        return False
    return 0 <= age <= 120

def validate_weight(weight):
    try:
        w = float(weight)
    except ValueError:
        return False
    return 0 <= w <= 300

def validate_country(country):
    # Not used in Urban Mobility; keep strict if referenced
    return bool(re.match(r"^[A-Z][A-Za-z]+$", country)) and len(country) <= 30
