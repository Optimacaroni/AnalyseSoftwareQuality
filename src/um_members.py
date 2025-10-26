import engineer
import admin

import sqlite3
import database

import bcrypt
from getpass import getpass
from safe_data import private_key, decrypt_data

from log_config import logmanager as log_manager
log_instance = log_manager()

import time
from ui_helpers import clear as ui_clear
from validation import validate_password


def main():
    log_instance.log_activity("System", "Program started", "No", "No")
    database.create_or_connect_db()
    main_menu()


def main_menu():
    while True:
        clear()
        print("\n--- Main Menu ---")
        print("1. Login")
        print("2. Password recovery")
        print("3. Exit")
        choice = input("Choose an option (1/2/3): ").strip()

        if choice == "1":
            Login()
        elif choice == "2":
            password_recovery_menu()
        elif choice == "3":
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
    ui_clear()


def password_recovery_menu():
    while True:
        ui_clear()
        print("\n--- Password Recovery ---")
        print("1. Request recovery token")
        print("2. Reset password using token")
        print("3. Go back")
        choice = input("Choose an option (1/2/3): ").strip()
        if choice == "1":
            request_recovery_token()
        elif choice == "2":
            reset_password_with_token()
        elif choice == "3":
            break
        else:
            print("Invalid input")
            time.sleep(1)


def request_recovery_token():
    ui_clear()
    print("\n--- Request Recovery Token ---")
    username = input("Enter your username: ").strip().lower()
    token = database.create_recovery_token_for_username(username)
    if token:
        print("If the account exists, a recovery token has been generated and will expire in 15 minutes.")
        print("Recovery token (showing because email not configured):", token)
        log_instance.log_activity(username, "Password recovery requested", "Recovery token generated", "No")
    else:
        print("If the account exists, a recovery token has been generated and will expire in 15 minutes.")
        log_instance.log_activity(username, "Password recovery requested", "Recovery token generation attempted", "No")
    input("Press Enter to continue...")


def reset_password_with_token():
    ui_clear()
    print("\n--- Reset Password Using Token ---")
    username = input("Enter your username: ").strip().lower()
    token = input("Enter recovery token: ").strip()
    if not database.verify_and_consume_recovery_token(username, token):
        ui_clear()
        print("Invalid or expired token.")
        log_instance.log_activity(username, "Password recovery", "Invalid or expired token provided", "No")
        time.sleep(2)
        return

    while True:
        new_password = getpass("Enter your new password: ")
        if not validate_password(new_password):
            print("Password does not meet complexity requirements.")
            time.sleep(1)
            continue
        confirm = getpass("Confirm new password: ")
        if new_password != confirm:
            print("Passwords do not match. Try again.")
            time.sleep(1)
            continue
        break

    conn = sqlite3.connect("scooterfleet.db")
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM Users")
    rows = cur.fetchall()
    target_enc = None
    for _rid, enc_uname in rows:
        try:
            if decrypt_data(private_key(), enc_uname).lower() == username:
                target_enc = enc_uname
                break
        except Exception:
            continue

    if not target_enc:
        ui_clear()
        print("User not found")
        log_instance.log_activity(username, "Password recovery", "User not found during reset", "Yes")
        time.sleep(2)
        conn.close()
        return

    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    cur.execute("UPDATE Users SET password = ? WHERE username = ?", (hashed, target_enc))
    conn.commit()
    conn.close()
    ui_clear()
    print("Password reset successfully")
    log_instance.log_activity(username, "Password recovery", "Password reset using recovery token", "No")
    time.sleep(2)


if __name__ == "__main__":
    main()
