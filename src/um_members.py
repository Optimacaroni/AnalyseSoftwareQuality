# Accountlevels
import engineer
import admin
# Hard-coded super admin credentials (avoid importing super_admin to prevent circular import)
super_username = "super_admin"
super_password = "Admin_123?"

# database
import sqlite3
import database

# cryptography and hashing
import bcrypt
from getpass import getpass
from safe_data import *

# logging
from log_config import logmanager as log_manager
log_instance = log_manager()

from search import *

from os import system, name
import time


def main():
    log_instance.log_activity("System", "Program started", "No", "No")
    database.create_or_connect_db()
    main_menu()


def main_menu():
    while True:
        clear()
        print("\n--- Main Menu ---")
        print("1. Login")
        print("2. Exit")
        choice = input("Choose an option (1/2): ").strip()

        if choice == "1":
            Login()
        elif choice == "2":
            print("Exiting the program. Goodbye!")
            log_instance.log_activity("System", "Program exited", "No", "No")
            break
        else:
            print("Invalid input")
            log_instance.log_activity("System", "Invalid input in the main menu", "No", "No")
            time.sleep(2)


def Login():
    max_attempts = 3
    attempts = 0

    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()
    cursor.execute("SELECT username, password, first_name, last_name, role_level FROM Users")
    data = cursor.fetchall()

    while attempts < max_attempts:
        clear()
        print("\n--- Login ---")
        username_input = input("Enter your username: ").strip().lower()
        password_input = getpass("Enter your password: ")

        user_data = []
        for user in data:
            decrypted_username = decrypt_data(private_key(), user[0]).lower()
            if decrypted_username == username_input:
                user_data = user
                break

        if user_data:
            decrypted_username = decrypt_data(private_key(), user_data[0])
            stored_hash = user_data[1]
            first_name = decrypt_data(private_key(), user_data[2])
            last_name = decrypt_data(private_key(), user_data[3])
            role_level = user_data[4]

            if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
                attempts = 0
                if role_level == "service_engineer":
                    log_instance.log_activity(decrypted_username, "Login successful", f"{first_name} {last_name} (service engineer) logged in", "No")
                    engineer.menu(decrypted_username)
                elif role_level == "system_admin":
                    log_instance.log_activity(decrypted_username, "Login successful", f"{first_name} {last_name} (system admin) logged in", "No")
                    admin.menu(decrypted_username)
                break
            else:
                attempts += 1
                print("Login failed")
                if attempts >= max_attempts:
                    print("You have reached the maximum number of login attempts")
                    log_instance.log_activity(decrypted_username, "Login failed", "Entered invalid password multiple times", "Yes")
                else:
                    log_instance.log_activity(decrypted_username, "Login failed", "Entered invalid password", "No")
        elif username_input == super_username and password_input == super_password:
            log_instance.log_activity(super_username, "Login successful", "Super admin logged in", "No")
            # import here to avoid circular import at module level
            import super_admin
            super_admin.menu()
            break
        else:
            attempts += 1
            if attempts >= max_attempts:
                print("You have reached the maximum number of login attempts")
                log_instance.log_activity(username_input, "Login failed", "Entered invalid username multiple times", "Yes")
            else:
                log_instance.log_activity(username_input, "Login failed", "Inputted an invalid username", "No")
            print("User not found")

        time.sleep(2)
    connection.close()


def clear():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


if __name__ == "__main__":
    main()
