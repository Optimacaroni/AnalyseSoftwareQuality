import re
import datetime
import database



def validate_first_name(first_name):
    pattern = r"^[A-Za-z][A-Za-z'\-]{0,29}$"
    return bool(re.match(pattern, first_name))

def validate_last_name(last_name):
    pattern = r"^[A-Za-z][A-Za-z'\-]*(?: [A-Za-z'\-]+)*$"
    return bool(re.match(pattern, last_name)) and len(last_name) <= 40

def validate_birthday(birthday):
    try:
        datetime.datetime.strptime(birthday, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_gender(gender):
    return gender in ("Male", "Female")

def validate_street(street):
    pattern = r"^[A-Za-z]+(?:[ -][A-Za-z]+)*$"
    return bool(re.match(pattern, street)) and len(street) <= 50

def validate_house_number(house_number):
    try:
        n = int(house_number)
        return 0 < n <= 10000
    except ValueError:
        return False

def validate_postal_code(postal_code):
    pattern = r"^[1-9][0-9]{3}[A-Z]{2}$"
    return bool(re.match(pattern, postal_code))

def validate_city(city):
    return city in database.Cities

def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+\-']+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email)) and len(email) <= 50

def validate_phone_number(phone_number):
    return bool(re.match(r"^[0-9]{8}$", phone_number))

def validate_driving_license(lic):
    return bool(re.match(r"^([A-Z]{2}\d{7}|[A-Z]{1}\d{8})$", lic))

def validate_username(username):
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_'.]{7,9}$", username))

def validate_password(password):
    special = r"~!@#$%&_\-+=`|\()\{\}\[\]:;'<>,\.?/"
    pattern = rf"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[{re.escape(special)}]).{{12,30}}$"
    return bool(re.match(pattern, password))