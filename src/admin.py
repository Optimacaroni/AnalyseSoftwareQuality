# System admin.
import sqlite3

from getpass import getpass
import bcrypt

import time

import um_members
from super_admin import scooter_menu, service_engineer_menu, system_menu, traveller_menu, list_users
from safe_data import private_key, decrypt_data
from validation import validate_password

# logging
from log_config import logmanager as log_manager
log_instance = log_manager()

def menu(username):
    while True:
        um_members.clear()
        print("\n--- System Admin Menu ---")
        print(f"--Welcome {username}--")
        log_instance.show_notifications()
    #Own account
        print("1. Update password")
        print("2. List of users")
        print("3. Service engineer menu")
        print("4. System")
        print("5. Traveller menu")
        print("6. Scooter menu")
        print("7. Logout")

        choice = input("Choose an option (1/2/3/4/5/6/7): ").strip()

        if choice == "1":
            um_members.clear()
            update_password(username)
        elif choice == "2":
            um_members.clear()
            list_users(username)
        elif choice == "3":
            um_members.clear()
            service_engineer_menu(username)
        elif choice == "4":
            system_menu(username, role="system_admin")
        elif choice == "5":
            um_members.clear()    
            traveller_menu(username)
        elif choice == "6":
            um_members.clear()
            scooter_menu(username, role="system_admin")
        elif choice == "7":
            print("You logged out, Goodbye!")
            log_instance.log_activity(username, "System", "Program exited", "No")
            break
        else:
            um_members.clear()
            log_instance.log_activity(username, "System", "Invalid input at the modifying menu", "No")
            time.sleep(2)

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

        # check if have reached end of loop
        if i == len(user_data) - 1:
            print("User not found")
            log_instance.log_activity(username, "Update password", "Nonexistent service engineer tried to update password", "Yes")
            exit()
            
    # Check if password is correct
    input_password = getpass("Enter your current password: ")
    if not bcrypt.checkpw(input_password.encode('utf-8'), found_password):
        log_instance.log_activity(username, "Update password", "Incorrect password", "No")
        return False
    else:
        while True:
            um_members.clear()
            print("\n--- Update Password ---")
            new_password = getpass("Enter your new password: ")
            if new_password == input_password:
                um_members.clear()
                print("New password must be different from the old password.")
                log_instance.log_activity(username, "Update password", "Entered same password as the old password", "No")
                time.sleep(2)
                continue
            if not validate_password(new_password):
                um_members.clear()
                print("Password does not meet complexity requirements.")
                log_instance.log_activity(username, "Update password", "Invalid new password (complexity)", "No")
                time.sleep(2)
                continue
            confirm_password = getpass("Confirm new password: ")
            if confirm_password != new_password:
                um_members.clear()
                print("Passwords do not match. Please try again.")
                log_instance.log_activity(username, "Update password", "Password confirmation mismatch", "No")
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


