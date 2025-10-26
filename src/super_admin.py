# Database
import sqlite3
import database

# Own modules
import um_members
import traveller
import user
import scooter_logic
# Validation
from validation import *

# Logging
from log_config import logmanager as log_manager
log_instance = log_manager()

# cryptography and hashing
import bcrypt
from safe_data import *

# search
from search import *

# centralized ACL
from acl import require_role

from ui_helpers import prompt_with_back, clear as ui_clear

import time
import datetime
import random
import zipfile
import os
import shutil
import secrets
import string

# scooter logic (add/modify/delete scooter)
from scooter_logic import add_scooter, modify_scooter, delete_scooter

# Hardcoded gegevens
super_username="super_admin"
super_password="Admin_123?"

def menu():
    um_members.clear()
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    while True:
        um_members.clear()
        log_instance.show_notifications()
        print("\n--- Super Administrator Menu ---")
        print(f"--Welcome super admin--\n")
        print("1. List of users")
        print("2. Service engineer menu")
        print("3. System admin menu")
        print("4. System")
        print("5. Traveller menu")
        print("6. Scooter menu")
        print("7. Logout")
        choice = input("Choose an option (1/2/3/4/5/6/7): ").strip()

        if choice == "1":
            um_members.clear()
            list_users(super_username)
        elif choice == "2":
            um_members.clear()
            service_engineer_menu(super_username)
        elif choice == "3":
            um_members.clear()
            systemadmin_menu(super_username)
        elif choice == "4":
            um_members.clear()
            system_menu(super_username, role="super_admin")
        elif choice == "5":
            um_members.clear()
            traveller_menu(super_username)
        elif choice == "6":
            um_members.clear()
            scooter_menu(super_username, role="super_admin")
        elif choice == "7":
            print("You logged out, Goodbye!")
            log_instance.log_activity(super_username, "System", "Program exited", "No")
            break
        else:
            print("Invalid input")
            log_instance.log_activity(super_username, "System", "Invalid input in the main menu", "No")
            time.sleep(2)
            connection.close()

def list_users(_username, role_filter=None):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    if role_filter:
        cursor.execute("SELECT id, username, role_level FROM users WHERE role_level =?" ,(role_filter,))
    else:
        cursor.execute("SELECT id, username, role_level FROM Users")
    user_data = cursor.fetchall()

    decrypted_user_data = []
    for id, username, role in user_data:
        decrypted_username = decrypt_data(private_key(), username)
        decrypted_user_data.append((id, decrypted_username, role))
    # Reuse the paginated display used by search results so layout is consistent across lists
    search_results = []
    search_results.append(["ID", "USERNAME", "ROLE"])
    for id, uname, role in decrypted_user_data:
        search_results.append([id, uname, role])

    um_members.clear()
    print("\n--- List of users ---")
    # show_numbers=False because this is a pure listing (no selection expected)
    display_search_results(search_results, show_numbers=False)
    input("Press Enter to return...")
    connection.close()

def service_engineer_menu(username):
    while True:
        um_members.clear()
        print("\n--- Service Engineer menu ---")
        print("1. Make a new service engineer")
        print("2. Modify service engineer")
        print("3. Delete a service engineer")
        print("4. Reset password of a service engineer")
        print("5. Go back")

        choice = input("Choose an option (1/2/3/4/5): ")
        
        if choice == "1":
            print("Make a new service engineer")
            user.create_account("service_engineer")
            print("\nAdded a new service engineer")
            log_instance.log_activity(username, "Add service engineer", "Added a new service engineer", "No")
            time.sleep(2)
        elif choice == "2":
            um_members.clear()
            modify_user("service_engineer", username)
        elif choice == "3":
            um_members.clear()
            delete_user("service_engineer", username)
        elif choice == "4":
            um_members.clear()
            reset_pw("service_engineer", username)
        elif choice == "5":
            break

def systemadmin_menu(username):
    while True:
        um_members.clear()
        print("\n--- System admin menu ---")
        print("1. Make a new system admin")
        print("2. Modify admin")
        print("3. Delete an admin")
        print("4. Reset password of an admin")
        print("5. Go back")

        choice = input("Choose an option (1/2/3/4/5): ")

        if choice == "1":
            print("Make a new system admin")
            user.create_account("system_admin")
            print("\nAdded a new admin")
            log_instance.log_activity(username, "System admin created", "New system administrator created successfully", "No")
            time.sleep(2)
        elif choice == "2":
            um_members.clear()
            modify_user("system_admin", username)
        elif choice == "3":
            um_members.clear()
            delete_user("system_admin", username)
        elif choice == "4":
            um_members.clear()
            reset_pw("system_admin", username)
        elif choice == "5":
            break
        else:
            print("Invalid input")
            log_instance.log_activity(username, "System", "Invalid input in the admin menu", "No")

def system_menu(username, role):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()
    while True:
        um_members.clear()

        if not os.path.exists('backup'):
            os.makedirs('backup')
        backup_path = "backup/backup.sql"
        zip_path = "backup/backup.zip"
        log_dir = "logs"

        print("\n--- System menu ---")
        print("1. Make a backup")
        print("2. Restore backup")
        if role == "super_admin":
            print("3. Generate one-use restore code for system admin")
            print("4. Revoke a restore code")
            print("5. See logs")
            print("6. Go back")
        else:
            print("3. See logs")
            print("4. Go back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            create_zip(backup_path, log_dir, zip_path)
            print("Backup created")
            log_instance.log_activity(username, "System", "Backup created", "No")
            time.sleep(2)
        elif choice == "2":
            if role == "super_admin":
                restore_backup("scooterfleet.db", zip_path)
                log_instance.log_activity(username, "System", "Backup restored", "No")
            else:
                code = input("Enter restore code: ").strip()
                cursor.execute("SELECT id, admin_user_id, backup_filename, used FROM RestoreCodes WHERE code = ?", (code,))
                row = cursor.fetchone()
                if not row:
                    print("Invalid code.")
                    log_instance.log_activity(username, "System", "Invalid restore code attempt", "Yes")
                else:
                    code_id, admin_user_id, backup_filename, used = row
                    cursor.execute("SELECT id, username FROM Users WHERE role_level='system_admin'")
                    admins = cursor.fetchall()
                    current_admin_id = None
                    for aid, enc_uname in admins:
                        if decrypt_data(private_key(), enc_uname) == username:
                            current_admin_id = aid
                            break
                    if used or current_admin_id != admin_user_id:
                        print("Restore code not valid for this account or already used.")
                        log_instance.log_activity(username, "System", "Restore code invalid/used", "Yes")
                    else:
                        restore_backup("scooterfleet.db", backup_filename)
                        cursor.execute("UPDATE RestoreCodes SET used = 1 WHERE id = ?", (code_id,))
                        connection.commit()
                        log_instance.log_activity(username, "System", "Backup restored using restore code", "No")
            time.sleep(2)
        elif choice == "3" and role == "super_admin":
            admin_username = input("Enter system admin username to authorize: ").strip().lower()
            cursor.execute("SELECT id, username FROM Users WHERE role_level = 'system_admin'")
            admins = cursor.fetchall()
            target_id = None
            for aid, enc_uname in admins:
                if decrypt_data(private_key(), enc_uname).lower() == admin_username:
                    target_id = aid
                    break
            if not target_id:
                print("System admin not found.")
                time.sleep(2)
                continue
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            code_zip = f"backup/backup_{int(time.time())}.zip"
            create_zip(backup_path, log_dir, code_zip)
            cursor.execute("INSERT INTO RestoreCodes (code, admin_user_id, backup_filename, used) VALUES (?, ?, ?, 0)", (code, target_id, code_zip))
            connection.commit()
            print(f"Restore code generated: {code}\nLinked backup: {code_zip}")
            log_instance.log_activity(username, "System", f"Generated restore code for {admin_username}", "No")
            input("Press Enter to continue...")
        elif (choice == "4" and role == "super_admin") or (choice == "3" and role != "super_admin"):
            if role == "super_admin":
                code = input("Enter code to revoke: ").strip()
                cursor.execute("DELETE FROM RestoreCodes WHERE code = ?", (code,))
                connection.commit()
                print("Restore code revoked (if existed).")
                log_instance.log_activity(username, "System", "Restore code revoked", "No")
                time.sleep(2)
            else:
                date = input("Keep empty for today's logs or enter date (yyyy-mm-dd): ").strip()
                um_members.clear()
                log_instance.see_logs(date)
        elif (choice == "5" and role == "super_admin") or (choice == "4" and role != "super_admin"):
            if role == "super_admin":
                date = input("Keep empty for today's logs or enter date (yyyy-mm-dd): ").strip()
                um_members.clear()
                log_instance.see_logs(date)
            else:
                break
        elif (choice == "6" and role == "super_admin"):
            break
        else:
            print("Invalid input")
            log_instance.log_activity(username, "System", "Invalid input in the system menu", "No")
            time.sleep(2)
    connection.close()

def traveller_menu(username):
    while True:
        um_members.clear()
        print("\n--- Traveller menu ---")
        print("1. Register new traveller")
        print("2. Modify traveller")
        print("3. Delete traveller")
        print("4. Search traveller")
        print("5. Go back")

        choice = input("Choose an option (1/2/3/4/5): ")

        if choice == "1":
            um_members.clear()
            add_traveller(username)
        elif choice == "2":
            um_members.clear()
            modify_user("traveller", username)
        elif choice == "3":
            um_members.clear()
            delete_user("traveller", username)
        elif choice == "4":
            search_people("traveller", username)
        elif choice == "5":
            break
        else:
            print("Invalid input")
            log_instance.log_activity(username, "Traveller menu", "Invalid input in the traveller menu", "No")

def scooter_menu(username, role):
    while True:
        um_members.clear()
        print("\n--- Scooter menu ---")
        print("1. Add scooter" if role != "service_engineer" else "")
        print("2. Modify scooter")
        print("3. Delete scooter" if role != "service_engineer" else "")
        print("4. Search scooter")
        print("5. Go back")
        choice = input("Choose an option: ").strip()

        if choice == "1" and role != "service_engineer":
            scooter_logic.add_scooter(username)
        elif choice == "2":
            scooter_logic.modify_scooter(username, role)
        elif choice == "3" and role != "service_engineer":
            scooter_logic.delete_scooter(username)
        elif choice == "4":
            search_people("scooter", username)
        elif choice == "5":
            break
        else:
            print("Invalid input")
            time.sleep(2)

def modify_data(datatype_to_update, table_to_update, id_to_update, new_data) -> bool:
    # Validate & prepare the value using centralized helper
    try:
        value = database.validate_and_prepare_value(table_to_update, datatype_to_update, new_data)
    except ValueError as e:
        print(str(e))
        return False

    # Determine id field
    if table_to_update == "Users":
        id_field = "id"
    elif table_to_update == "Travellers":
        id_field = "customer_id"
    else:
        id_field = "scooter_id"

    try:
        ok = database.update_column(table_to_update, datatype_to_update, id_field, id_to_update, value)
    except Exception as e:
        print(f"Update failed: {e}")
        time.sleep(2)
        return False

    if not ok:
        print(f"No rows found with id {id_to_update}.")
        time.sleep(2)
        return False

    return True

def modify_user(role, username):
    while True:
        um_members.clear()
        print("\n--- Update ---")
    
        if role in ["system_admin", "service_engineer"]:
            search_term = prompt_with_back("Enter search term: ")
            # Enter or 'b' cancels/back
            if search_term is None:
                break
            search_results = search(search_term, "Users", role=role)
            choice = display_search_results(search_results, show_numbers=True, allow_select=True)
            if choice is None:
                print("Operation canceled.")
                break
            if 1 <= choice <= len(search_results) - 1:
                selected_result = search_results[choice]
                um_members.clear()
            else:
                um_members.clear()
                print("Invalid choice. Please select a valid number.")
                time.sleep(2)
                continue
            
            while True:
                print(f"Selected user: {selected_result[1]}")
                print("\n 1. Username")
                print(" 2. First name")
                print(" 3. Last name")
                choice = prompt_with_back("\nChoose the field you want to change (1/2/3) (press Enter to go back): ")
                # prompt_with_back returns None for Enter or 'b'
                if choice is None:
                    ui_clear()
                    break
                if choice == "1":
                    new_data = input("Enter new username: ").strip().lower()
                    if validate_username(new_data):
                        if modify_data("username", "Users", selected_result[0], new_data):
                            um_members.clear()
                            print("Username updated successfully")
                            time.sleep(2)
                            break
                        else:
                            print("Username not updated")
                            continue
                    else:
                        print("Invalid input")
                        time.sleep(2)
                        um_members.clear()
                        continue
                elif choice == "2":
                    new_first_name = input("Enter new first name: ").strip()
                    if validate_first_name(new_first_name):
                        if modify_data("first_name", "Users", selected_result[0], new_first_name):
                            um_members.clear()
                            print("First name updated successfully")
                            time.sleep(2)
                            break
                        else:
                            print("First name not updated")
                            continue 
                    else:
                        print("Invalid input")
                        time.sleep(2)
                        um_members.clear()
                        continue
                elif choice == "3":
                    new_data = input("Enter new last name: ").strip()
                    if validate_last_name(new_data):
                        if modify_data("last_name", "Users", selected_result[0], new_data):
                            um_members.clear()
                            print("Last name updated successfully")
                            time.sleep(2)
                            break
                        else:
                            print("Last name not updated")
                            continue
                    else:
                        print("Invalid input")
                        time.sleep(2)
                        um_members.clear()
                        continue
                else:
                    print("Invalid input")
                    time.sleep(2)
                    um_members.clear()
                    continue
        
        elif role == "traveller":
            search_term = prompt_with_back("Enter search term: ")
            # Enter or 'b' cancels/back
            if search_term is None:
                break
            search_results = search(search_term, "Travellers")
            if (len(search_results) == 0):
                um_members.clear()
                print("No travellers found")
                time.sleep(2)
                return
            else:
                traveller_to_update = show_travellers(search_results[1:], username, from_modify=True)
                if traveller_to_update is None:
                    break
                while True:
                    um_members.clear()
                    print("\n 1. First name")
                    print(" 2. Last name")
                    print(" 3. Birthday")
                    print(" 4. Gender")
                    print(" 5. Street")
                    print(" 6. House number")
                    print(" 7. Zip code")
                    print(" 8. City")
                    print(" 9. Email")
                    print("10. Mobile phone")
                    print("11. Driving license number")
                    choice = prompt_with_back("Choose field to change (1-11 or 'b' to go back) (press Enter to go back): ")
                    if choice is None:
                        ui_clear()
                        break
                    choice = choice.lower()
                    field_map = {
                        "1": ("first_name", validate_first_name),
                        "2": ("last_name", validate_last_name),
                        "3": ("birthday", validate_birthday),
                        "4": ("gender", validate_gender),
                        "5": ("street_name", validate_street),
                        "6": ("house_number", validate_house_number),
                        "7": ("zip_code", validate_postal_code),
                        "8": ("city", validate_city),
                        "9": ("email", validate_email),
                        "10":("mobile_phone", validate_phone_number),
                        "11":("driving_license_number", validate_driving_license),
                    }
                    if choice not in field_map:
                        print("Invalid input")
                        time.sleep(2)
                        um_members.clear()
                        continue
                    field, validator = field_map[choice]
                    new_data = input("Enter new value: ").strip()
                    if field == "mobile_phone":
                        if not validator(new_data):
                            print("Invalid input")
                            time.sleep(2)
                            um_members.clear(); continue
                        new_data = "+31-6-" + new_data
                    elif not validator(new_data):
                        print("Invalid input")
                        time.sleep(2)
                        um_members.clear(); continue
                    if modify_data(field, "Travellers", traveller_to_update, new_data):
                        um_members.clear()
                        print("Traveller updated successfully")
                        log_instance.log_activity(username, "Modify traveller", f"Updated {field} of traveller id: {traveller_to_update}", "No")
                        time.sleep(2)
                        break
            return
            
        else:
            um_members.clear()
            print("Invalid input")
            log_instance.log_activity(username, "Modify user", "Invalid input in the modify user menu", "No")
            time.sleep(2)

@require_role('system_admin')
def delete_user(role, username):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    while True:
        print(f"\n--- Delete {role} ---")
        # Handle travellers using a numbered selection flow similar to delete_scooter
        if role == "traveller":
            term = prompt_with_back("Enter search term: ")
            # Enter or 'b' cancels/back
            if term is None:
                break
            results = search(term, "Travellers")
            if not results:
                print("No travellers found")
                time.sleep(2)
                break
            display_search_results(results, show_numbers=True)
            choice_input = prompt_with_back("Enter the number of the traveller to delete: ")
            if choice_input is None:
                break
            try:
                choice = int(choice_input.strip())
            except ValueError:
                ui_clear()
                print("Invalid input")
                time.sleep(2)
                break
            if choice < 1 or choice > len(results)-1:
                print("Invalid choice")
                time.sleep(2)
                break
            selected = results[choice]
            cust_id = selected[0]
            # Try to decrypt some identifying fields for clarity
            try:
                first = decrypt_data(private_key(), selected[1]) if isinstance(selected[1], (bytes, bytearray)) else selected[1]
            except Exception:
                first = selected[1]
            try:
                last = decrypt_data(private_key(), selected[2]) if isinstance(selected[2], (bytes, bytearray)) else selected[2]
            except Exception:
                last = selected[2]
            print(f"Selected traveller: {cust_id} - {first} {last}")
            confirm = input(f"Are you sure you want to delete traveller {cust_id}? (y/n): ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Delete cancelled")
                time.sleep(1)
                break
            cursor.execute("DELETE FROM Travellers WHERE customer_id = ?", (cust_id,))
            connection.commit()
            print(f"{role.capitalize()} deleted successfully")
            log_instance.log_activity(username, "Delete traveller", f"Deleted traveller with id: {cust_id}", "No")
            time.sleep(2)
            break

        # Non-traveller flows (users/admins) - use existing search_people for consistency
        else:
            search_results = search_people(role, username)

            if not search_results:
                print(f"No {role}s found")
                time.sleep(2)
                break

            choice = display_search_results(search_results, show_numbers=True, allow_select=True)
            if choice is None:
                break
            try:
                if choice < 1 or choice > len(search_results)-1:
                    um_members.clear()
                    print("Invalid choice. Please select a valid number.")
                    time.sleep(2)
                    continue
            except Exception:
                um_members.clear()
                print("Please enter a valid number.")
                time.sleep(2)
                continue
            # At this point we have a validated numeric choice; perform deletion
            selected = search_results[choice]
            selected_id = selected[0]
            confirm = input(f"Are you sure you want to delete user id {selected_id}? (y/n): ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Delete cancelled")
                time.sleep(1)
                break
            cursor.execute("DELETE FROM Users WHERE id = ?", (selected_id,))
            connection.commit()
            print("User deleted successfully")
            # Try to decrypt username for logging if possible
            try:
                enc_uname = selected[1]
                dec_uname = decrypt_data(private_key(), enc_uname)
            except Exception:
                dec_uname = str(selected_id)
            log_instance.log_activity(username, "Delete user", f"Deleted user id: {selected_id}, username: {dec_uname}", "No")
            time.sleep(2)
            break

def reset_pw(role, username):
    um_members.clear()
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()
    
    while True:
        print(f"\n--- Reset password of {role} ---")
        search_results = search_people(role, username)

        if not search_results:
            print(f"No {role}s found")
            time.sleep(2)
            break

        if role in ["system_admin", "service_engineer"]:
            display_search_results(search_results, show_numbers=False)

        pw_to_reset = prompt_with_back(f"\nEnter the id of the {role} for the password you want to reset: ")
        if pw_to_reset is None:
            break
        try:
            pw_to_reset = int(pw_to_reset)
            selected_user = None
            for result in search_results:
                if result[0] == pw_to_reset:
                    selected_user = result
                    break
            if not selected_user:
                um_members.clear()
                print("Invalid choice. Please select a valid number.")
                time.sleep(2)
                continue
        except ValueError:
            print("Please enter a number.")
            time.sleep(2)
            continue
        
        cursor.execute("SELECT username, password FROM Users WHERE id = ? AND role_level = ?", (pw_to_reset, role))
        user_to_change = cursor.fetchall()

        if not user_to_change:
            um_members.clear()
            print("User not found")
            log_instance.log_activity(username, "Reset password", "Nonexistent user tried to reset password", "No")
            time.sleep(2)
            continue
        else:
            decrypted_name = decrypt_data(private_key(), user_to_change[0][0])
            cursor.execute("UPDATE Users SET password = ? WHERE id = ?", (bcrypt.hashpw("Temp_123?456".encode('utf-8'), bcrypt.gensalt()), pw_to_reset))
            connection.commit()
            print("Password reset successfully")
            log_instance.log_activity(username, "Reset password", f"Reset password of {role} with username: {decrypted_name}", "No")
            time.sleep(2)
            break

@require_role('system_admin')
def add_traveller(username):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    um_members.clear()
    print("\n--- Register Traveller ---")

    # Input and validation
    first_name = input_and_validate("Enter first name: ", validate_first_name)
    last_name = input_and_validate("Enter last name: ", validate_last_name)
    birthday = input_and_validate("Enter birthday (YYYY-MM-DD): ", validate_birthday)
    gender = input_and_validate("Enter gender (Male/Female): ", validate_gender)
    um_members.clear()
    street = input_and_validate("Enter street: ", validate_street)
    house_number = input_and_validate("Enter house number: ", validate_house_number)
    zip_code = input_and_validate("Enter zip code (e.g., 1234AB): ", validate_postal_code)
    # Show predefined cities and require selection by number only
    from database import Cities as PREDEFINED_CITIES
    print("Choose city from the list below (enter the number):")
    for i, c in enumerate(PREDEFINED_CITIES, start=1):
        print(f"{i}. {c}")
    while True:
        city_input = input("Enter city number: ").strip()
        if city_input.isdigit():
            idx = int(city_input)
            if 1 <= idx <= len(PREDEFINED_CITIES):
                city = PREDEFINED_CITIES[idx-1]
                break
        print("Invalid selection. Choose a number from the list.")
    um_members.clear()
    email = input_and_validate("Enter email: ", validate_email)
    mobile = input_and_validate("Enter 8-digit mobile (DDDDDDDD): ", validate_phone_number)
    driving_license = input_and_validate("Enter driving license (XXDDDDDDD or XDDDDDDDD): ", validate_driving_license)

    #  Unique customer_id (YY + 8 random + checksum)
    current_date = str(datetime.datetime.now().year)
    customer_id = current_date[-2:]
    checksum = sum(int(d) for d in customer_id)
    for _ in range(7):
        rn = random.randint(0, 9)
        customer_id += str(rn)
        checksum += rn
    checksum %= 10
    customer_id += str(checksum)

    # Prepare and validate fields using centralized helper which handles encryption
    data = (
        customer_id,
        database.validate_and_prepare_value('Travellers', 'first_name', first_name),
        database.validate_and_prepare_value('Travellers', 'last_name', last_name),
        database.validate_and_prepare_value('Travellers', 'birthday', birthday),
        database.validate_and_prepare_value('Travellers', 'gender', gender),
        database.validate_and_prepare_value('Travellers', 'street_name', street),
        database.validate_and_prepare_value('Travellers', 'house_number', house_number),
        database.validate_and_prepare_value('Travellers', 'zip_code', zip_code),
        database.validate_and_prepare_value('Travellers', 'city', city),
        database.validate_and_prepare_value('Travellers', 'email', email),
        database.validate_and_prepare_value('Travellers', 'mobile_phone', "+31-6-" + mobile),
        database.validate_and_prepare_value('Travellers', 'driving_license_number', driving_license)
    )

    cursor.execute("""
        INSERT INTO Travellers (
            customer_id, first_name, last_name, birthday, gender, street_name,
            house_number, zip_code, city, email, mobile_phone, driving_license_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    connection.commit()
    connection.close()

    um_members.clear()
    print("Traveller registered successfully")
    log_instance.log_activity(username, "Add traveller", f"Added traveller: '{first_name} {last_name}'", "No")
    time.sleep(2)
    return (first_name, last_name)

def input_and_validate(prompt, validate_func, default_value=""):
    while True:
        data = default_value or input(prompt).strip()
        if validate_func(data):
            return data
        else:
            print("Invalid input provided.")
            log_instance.log_activity("System", "Invalid input", "Validation did not pass", "No")

def search_people(role, username):
    um_members.clear()
    search_term = prompt_with_back("Enter search term: ")
    # If user pressed Enter or 'b', treat as no results / cancel
    if search_term is None:
        um_members.clear()
        if role == "traveller":
            print("No travellers found")
        elif role in ["system_admin", "service_engineer"]:
            print(f"No {role}s found")
        elif role == "scooter":
            print("No scooters found")
        else:
            print("No results found")
        time.sleep(2)
        return None
    if role == "traveller":
        search_results = search(search_term, "Travellers")
        if not search_results:
            print("No travellers found")
            time.sleep(2)
            return None
        else:
            id_to_update = show_travellers(search_results[1:], username, from_modify=False)
            return id_to_update
    elif role in ["system_admin", "service_engineer"]:
        search_results = search(search_term, "Users", role=role)
        if not search_results:
            print(f"No {role}s found")
            time.sleep(2)
            return None
        else:
            return search_results
    elif role == "scooter":
        search_results = search(search_term, "Scooters")
        display_search_results(search_results, show_numbers=False)
        input("Press Enter to continue...")
        return None
    else:
        um_members.clear()
        print("Invalid input")
        time.sleep(2)
        return None

def show_travellers(travellers, username, from_modify=False):
    if not travellers:
        um_members.clear()
        print("No travellers found")
        time.sleep(2)
        return None
    # Use centralized UI helper to normalize back/enter handling and clearing
    from ui_helpers import prompt_with_back, clear as ui_clear

    current = 0
    while True:
        ui_clear()
        print("\n--- Traveller Data ---")
        traveller.ShowData(travellers[current])

        print(f"\n--- page {current + 1} / {len(travellers)} ---")
        print("N. Next")
        print("P. Previous")
        print("B. Go back")

        if from_modify:
            print("\nEnter the pagenumber of the traveller (or N/P for another): ")

        choice = prompt_with_back("Choose an option: ")
        # prompt_with_back returns None when user pressed Enter or 'b'
        if choice is None:
            return None
        choice = choice.lower()
        if choice == "n":
            if current == len(travellers) - 1:
                print("You have reached the last page")
                time.sleep(2)
            else:
                current += 1
        elif choice == "p":
            if current == 0:
                print("You are already at the first page")
                time.sleep(2)
            else:
                current -= 1
        else:
            try:
                idx = int(choice) - 1
                if idx < 0 or idx >= len(travellers):
                    ui_clear()
                    print("Invalid input")
                    log_instance.log_activity(username, "Search traveller", "Invalid input in search traveller", "No")
                    time.sleep(2)
                    continue
                return travellers[idx][0]
            except ValueError:
                ui_clear()
                print("Invalid input")
                time.sleep(2)
                return None

def make_backup(backup_path):
    connection = sqlite3.connect("scooterfleet.db")
    with open(backup_path, 'w') as backup_file:
        for line in connection.iterdump():
            backup_file.write('%s\n' % line)
    connection.close()
    
def collect_log_files(log_dir, temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            modified_time = datetime.date.fromtimestamp(os.path.getmtime(filepath))
            if modified_time >= thirty_days_ago:
                shutil.copy(filepath, temp_dir)

def create_zip(backup_path, log_dir, zip_path):
    temp_dir = 'temp_logs'
    make_backup(backup_path)
    collect_log_files(log_dir, temp_dir)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(backup_path, os.path.basename(backup_path))
        for log_file in os.listdir(temp_dir):
            log_file_path = os.path.join(temp_dir, log_file)
            zipf.write(log_file_path, os.path.basename(log_file_path))
    shutil.rmtree(temp_dir)

def restore_backup(db_path, zip_path):
    if not os.path.exists(zip_path):
        print("No backup found")
        time.sleep(2)
        return
    else:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        database.clear_database()
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall('backup')
        backup_file_path = os.path.join('backup', 'backup.sql')
        with open(backup_file_path, 'r') as backup_file:
            sql_script = backup_file.read()
            cursor.executescript(sql_script)
        connection.commit()
        connection.close()
        if os.path.exists('backup'):
            for file in os.listdir('backup'):
                os.remove(os.path.join('backup', file))
            os.rmdir('backup')
        print("Backup restored")
        time.sleep(2)
