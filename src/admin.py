# System admin.
import sqlite3

from getpass import getpass
import bcrypt

import time

import um_members
from super_admin import *

# logging
from log_config import logmanager as log_manager
log_instance = log_manager()

def menu(username):
    um_members.clear()
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    cursor.execute("SELECT username, password, role_level FROM Users WHERE username =?", (username,))
    user_data = cursor.fetchone()

    while True:
        print("\n--- System Admin Menu ---")
        print(f"--Welcome {username}--")
        log_instance.show_notifications()
    #Own account
        print("1. Update password")
    #List of users
        print("2. List of users")
    #Add new service engineer
    #Modify, update service engineer
    #Delete service engineer
    #Give service engineer temp password
        print("3. Service engineer menu")
    #Backup, restore members info, users data
    #See logs
        print("4. System")
    #Add new traveller
    #Modify or update traveller
    #Delete traveller
    #Search, retrieve info of traveller
        print("5. Traveller menu")
    # logout
        print("6. Logout")

        choice = input("Choose an option (1/2/3/4/5/6): ").strip()

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
            print("You logged out, Goodbye!")
            log_instance.log_activity(username, "System", "Program exited", "No")
            break
        else:
            um_members.clear()
            log_instance.log_activity(username, "System", "Invalid input at the modifying menu", "No")
            time.sleep(2)

# Functions
def update_password(username): # TODO: Add validation
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    um_members.clear()
    print("\n--- Update Password ---")
    # Login with current password
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
                # enter password in database
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

                # Find encrypted username to update
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


