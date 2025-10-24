import sqlite3
from getpass import getpass
import bcrypt
import um_members
import time
from safe_data import *
from super_admin import *
# logging
from log_config import logmanager as log_manager
log_instance = log_manager()

def menu(username):
    um_members.clear()
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    cursor.execute("SELECT username, password FROM Users")
    user_rows = cursor.fetchall()
    user_data = None
    for row in user_rows:
        if decrypt_data(private_key(), row[0]) == username:
            user_data = row
            break

    while True:
        um_members.clear()
        print("\n--- Service Engineer Menu ---")
        print(f"--Welcome {username}--\n")
        print("1. Update password")
        print("2. Scooters menu")
        print("3. Logout")
        choice = input("Choose an option (1/2/3): ").strip()

        if choice == "1":
            um_members.clear()
            update_password(username)
        elif choice == "2":
            um_members.clear()
            scooter_menu(username, role="service_engineer")
        elif choice == "3":
            print("You logged out, Goodbye!")
            log_instance.log_activity(f"{username}", "System", "Logged out", "No")
            break
        else:
            log_instance.log_activity(f"{username}", "System", "Invalid input in the main menu", "No")

def update_password(username):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    um_members.clear()
    print("\n--- Update Password ---")
    cursor.execute("SELECT * FROM Users")
    user_data = cursor.fetchall()
    decrypted_username = ""
    found_password = ""
    for i in range(len(user_data)):
        decrypted_username = decrypt_data(private_key(), user_data[i][1])
        if decrypted_username == username:
            found_password = user_data[i][2]
            break
        if i == len(user_data) - 1:
            print("User not found")
            log_instance.log_activity(username, "Update password", "Nonexistent service engineer tried to update password", "Yes")
            exit()
            
    input_password = getpass("Enter your current password: ")
    if not bcrypt.checkpw(input_password.encode('utf-8'), found_password):
        log_instance.log_activity(username, "Update password", "Incorrect password", "No")
        return False
    else:
        while True:
            um_members.clear()
            print("\n--- Update Password ---")
            new_password = getpass("Enter your new password: ")
            if (new_password == input_password):
                um_members.clear()
                print("Invalid password")
                log_instance.log_activity(username, "Update password", "Entered same password as the old password", "No")
                time.sleep(2)
                continue
            elif (not validate_password(new_password)):
                um_members.clear()
                print("Invalid password")
                log_instance.log_activity(username, "Update password", "Invalid password", "No")
                time.sleep(2)
                continue
            else:
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute("SELECT * FROM Users")
                user_data = cursor.fetchall()
                decrypted_username = ""
                for i in range(len(user_data)):
                    decrypted_username = decrypt_data(private_key(), user_data[i][1])
                    if decrypted_username == username:
                        encrypted_username = user_data[i][1]
                        break
                cursor.execute("UPDATE Users SET password = ? WHERE username = ?", (hashed_password, encrypted_username))
                connection.commit()
                connection.close()
                um_members.clear()
                print("Password updated successfully")
                log_instance.log_activity(username, "Update password", f"Password updated successfully for user: '{username}'", "No")
                time.sleep(2)
                break
        return True
