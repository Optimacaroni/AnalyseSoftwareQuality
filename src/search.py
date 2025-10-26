import sqlite3
import re
import time
from safe_data import private_key, decrypt_data
from ui_helpers import clear as ui_clear, prompt_with_back

def _is_valid_identifier(name: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name))


ALLOWED_TABLES = {"USERS", "TRAVELLERS", "SCOOTERS", "RESTORECODES"}


def search(search_term, table, column="*", role=None):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()
    if search_term is None:
        search_term = ""
    search_term = str(search_term).strip()
    if search_term == "":
        return []

    table = table.upper()
    if table not in ALLOWED_TABLES:
        return f"Invalid table: {table}"

    cursor.execute(f"PRAGMA table_info({table})")
    columns_info = cursor.fetchall()
    columns = [info[1] for info in columns_info if "password" not in info[1].lower()]

    if not columns:
        return f"No columns found in {table}"

    if column != "*":
        column_candidate = column
        if not _is_valid_identifier(column_candidate):
            column = "*"
        else:
            matched = None
            for c in columns:
                if c.lower() == column_candidate.lower():
                    matched = c
                    break
            column = matched if matched else "*"

    if column == "*":
        columns_to_query = ", ".join(columns)
    else:
        if not _is_valid_identifier(column):
            return "Invalid column name"
        columns_to_query = column

    if role:
        query = f"SELECT {columns_to_query} FROM {table} WHERE role_level = ?"
        cursor.execute(query, (role,))
    else:
        query = f"SELECT {columns_to_query} FROM {table}"
        cursor.execute(query)

    all_data = cursor.fetchall()
    search_results = []
    search_results.append([col.upper() for col in columns])

    for row in all_data:
        decrypted_data = []
        for item in row:
            if isinstance(item, (bytes, bytearray)):
                try:
                    decrypted_data.append(decrypt_data(private_key(), item))
                except Exception:
                    decrypted_data.append(item)
            else:
                decrypted_data.append(item)
        if any(search_term.lower() in str(field).lower() for field in decrypted_data):
            search_results.append(decrypted_data)

    if len(search_results) == 1:
        return []
    return search_results

def display_search_results(search_results, show_numbers=True, rows_per_page=10, allow_select=False):
    print("--- Results ---")
    if type(search_results) == str:
        print(search_results)
        return None
    if not search_results or len(search_results) == 0:
        print("No results.")
        return None

    header_cols = search_results[0][:4] if len(search_results[0]) >= 4 else search_results[0]
    total_items = len(search_results) - 1
    total_pages = (total_items + rows_per_page - 1) // rows_per_page

    current_page = 0
    while True:
        start = current_page * rows_per_page
        end = start + rows_per_page
        page_items = search_results[1:][start:end]

        header = ("     " if show_numbers else "") + "".join(c.ljust(20) for c in header_cols)
        print(header)
        print("-" * len(header))

        for i, result in enumerate(page_items, start=start + 1):
            cols = result[:len(header_cols)]
            line = (f"[{i}]  " if show_numbers else "") + "".join(str(c).ljust(20) for c in cols)
            print(line)

        if total_pages == 1 and not allow_select:
            return None

        nav_parts = []
        if current_page > 0:
            nav_parts.append("P. Previous")
        if current_page < total_pages - 1:
            nav_parts.append("N. Next")
        if allow_select:
            nav_parts.append("Enter number to select")
        nav_parts.append("B. Go back")

        prompt = " | ".join(nav_parts) + ": "
        choice = prompt_with_back(prompt)

        if choice is None:
            return None

        if choice.lower() == 'p' and current_page > 0:
            current_page -= 1
            continue
        if choice.lower() == 'n' and current_page < total_pages - 1:
            current_page += 1
            continue
        if choice.lower() == 'b':
            return None
        if allow_select:
            try:
                sel = int(choice)
                if 1 <= sel <= total_items:
                    return sel
                else:
                    ui_clear()
                    print('Invalid selection')
                    time.sleep(2)
                    continue
            except ValueError:
                ui_clear()
                print('Invalid input')
                time.sleep(2)
                continue
        else:
            ui_clear()
            print('Invalid input')
            time.sleep(2)
            continue
