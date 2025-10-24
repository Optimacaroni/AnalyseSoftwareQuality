import sqlite3
import time
import bcrypt
from getpass import getpass
from safe_data import *
from validation import *
import um_members

# logging.
from log_config import logmanager as log_manager
log_instance = log_manager()

def create_account(role):
    while True:
        um_members.clear()
        print("\n--- Create Account ---")

        # username (case-insensitive uniqueness)
        while True:
            um_members.clear()
            userName = input("Enter a username: ").strip()
            if not validate_username(userName):
                print("Invalid username. Please try again.")
                time.sleep(2)
                log_instance.log_activity("", "Create account failed", "Invalid username", "No")
                continue
            normalized = userName.lower()

            connection = sqlite3.connect("scooterfleet.db")
            cursor = connection.cursor()
            cursor.execute("SELECT username FROM Users")
            all_usernames = cursor.fetchall()
            exists = False
            for (enc_uname,) in all_usernames:
                dec = decrypt_data(private_key(), enc_uname).lower()
                if dec == normalized:
                    exists = True
                    break
            if exists:
                print("Username already exists. Please choose another username.")
                log_instance.log_activity("", "Create account failed", "Entered already existing username", "No")
                connection.close()
                continue
            connection.close()
            break

        # password
        while True:
            um_members.clear()
            password = getpass("Enter a password: ")
            if validate_password(password):
                break
            else:
                print("Invalid password. Please try again.")
                time.sleep(2)
                log_instance.log_activity("", "Create account failed", "Invalid password", "No")

        # first name
        while True:
            um_members.clear()
            firstName = input("Enter your first name: ").strip()
            if validate_first_name(firstName):
                break
            print("Invalid first name. Please try again.")
            time.sleep(2)
            log_instance.log_activity("", "Create account failed", "Invalid first name", "No")

        # last name
        while True:
            um_members.clear()
            lastName = input("Enter your last name: ").strip()
            if validate_last_name(lastName):
                break
            print("Invalid last name. Please try again.")
            time.sleep(2)
            log_instance.log_activity("", "Create account failed", "Invalid last name", "No")

        if role == "service_engineer":
            roleLevel = "service_engineer"
        elif role == "system_admin":
            roleLevel = "system_admin"
        else:
            roleLevel = "service_engineer"

        hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # store normalized username
        enc_username = encrypt_data(public_key(), normalized)
        enc_firstName = encrypt_data(public_key(), firstName)
        enc_lastName = encrypt_data(public_key(), lastName)

        connection = sqlite3.connect("scooterfleet.db")
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO Users (username, password, first_name, last_name, role_level)
                          VALUES (?, ?, ?, ?, ?)""", (enc_username, hashedPassword, enc_firstName, enc_lastName, roleLevel))
        connection.commit()
        connection.close()
        log_instance.log_activity("", "Acount created", f"Account created successfully with the username: '{normalized}'", "No")
        break
