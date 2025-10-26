import logging
from logging.handlers import TimedRotatingFileHandler
import os
import base64
from safe_data import encrypt_data, public_key, decrypt_data, private_key

class logmanager:
    unread_suspicious_count = 0

    def __init__(self, log_dir="logs", log_file="scooterfleet.log"):
        self.log_dir = log_dir
        self.log_file_path = os.path.join(log_dir, log_file)
        self.unread_suspicious_count = 0 
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.logger = logging.getLogger('meal_logger')
        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.INFO)

            handler = TimedRotatingFileHandler(self.log_file_path, when='midnight', interval=1, backupCount=30)
            handler.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

    def log_activity(self, username, description, additional_info=None, suspicious='No'):
        raw_entry = f"{username} - {description} - {additional_info or ''} - Suspicious: {suspicious}"
        ciphertext = encrypt_data(public_key(), raw_entry)
        try:
            b64 = base64.b64encode(ciphertext).decode('ascii')
        except Exception:
            b64 = repr(ciphertext)

        if suspicious == 'Yes':
            self.logger.warning(b64)
            logmanager.unread_suspicious_count += 1
        else:
            self.logger.info(b64)

    def show_notifications(self):
        if logmanager.unread_suspicious_count > 0:
            print(f"\n*** You have {logmanager.unread_suspicious_count} unread suspicious activity logs. ***\n")
        else:
            print("\nNo unread suspicious acitivities.\n")

        
    def see_logs(self, date=None):

        file_path = self.log_file_path
        if date:
            file_path = f'{self.log_file_path}.{date}'

        import um_members

        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                total_lines = len(lines)
                pages = (total_lines + 19) // 20

                page = 0
                while True:
                    um_members.clear()
                    start_index = page * 20
                    end_index = min((page + 1) * 20, total_lines)
                    current_page_lines = lines[start_index:end_index]

                    for line in current_page_lines:
                        parts = line.split(" - ", 2)
                        decrypted = "<unreadable log entry>"
                        if len(parts) >= 3:
                            b64msg = parts[2].strip()
                            try:
                                try:
                                    ciphertext = base64.b64decode(b64msg)
                                except Exception:
                                    try:
                                        import ast as _ast
                                        ciphertext = _ast.literal_eval(b64msg)
                                    except Exception:
                                        ciphertext = None

                                if ciphertext:
                                    decrypted = decrypt_data(private_key(), ciphertext)
                                else:
                                    decrypted = b64msg
                            except Exception:
                                decrypted = "<unreadable log entry>"

                        ts = parts[0] if len(parts) > 0 else ''
                        level = parts[1] if len(parts) > 1 else ''
                        print(str(ts), "- ", end="")
                        print(str(level), "- ", end="")
                        print(decrypted)


                    print(f"\n--- Page {page + 1} / {pages} ---\n")
                    print("1. Next page")
                    print("2. Previous page")
                    print("3. Go back")
                    from ui_helpers import prompt_with_back, clear as ui_clear

                    choice = prompt_with_back("Choose an option (1/2/3): ")
                    if choice is None:
                        logmanager.unread_suspicious_count = 0
                        break

                    if choice == "1":
                        if page < pages - 1:
                            page += 1
                    elif choice == "2":
                        if page > 0:
                            page -= 1
                    elif choice == "3":
                        logmanager.unread_suspicious_count = 0
                        break
                    else:
                        ui_clear()
                        print("Invalid input")
                    
        except FileNotFoundError:
            print(f"The file {file_path} does not exist.")