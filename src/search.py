import sqlite3
import re
import time
from safe_data import *
from ui_helpers import clear as ui_clear, prompt_with_back

'''
How to use the search function:
-----------------------------------------------------
search_term:    the term you want to search for
table:          the table you want to search in
column:         only enter if you want to search in a specific column, otherwise leave empty

CODE EXAMPLE:
search_term = input("Enter search term: ")
search_results = search(search_term, table, column)
display_search_results(search_results)
-----------------------------------------------------
'''

def _is_valid_identifier(name: str) -> bool:
    # basic identifier validation: starts with letter or underscore, followed by letters/digits/underscores
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name))


# Whitelist of allowed tables (uppercase)
ALLOWED_TABLES = {"USERS", "TRAVELLERS", "SCOOTERS", "RESTORECODES"}


def search(search_term, table, column="*", role=None):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()
    # Normalize search_term: strip whitespace and handle empty input consistently
    if search_term is None:
        search_term = ""
    search_term = str(search_term).strip()
    if search_term == "":
        # Consistent empty result for empty/blank searches
        return []

    table = table.upper()
    # reject unknown or malicious table identifiers
    if table not in ALLOWED_TABLES:
        return f"Invalid table: {table}"

    # PRAGMA with validated table name
    cursor.execute(f"PRAGMA table_info({table})")
    columns_info = cursor.fetchall()
    columns = [info[1] for info in columns_info if "password" not in info[1].lower()]

    if not columns:
        return f"No columns found in {table}"

    if column != "*":
        # allow searching only in an existing column
        column_candidate = column
        if not _is_valid_identifier(column_candidate):
            column = "*"
        else:
            # match case-insensitive against PRAGMA columns
            matched = None
            for c in columns:
                if c.lower() == column_candidate.lower():
                    matched = c
                    break
            column = matched if matched else "*"

    # build safe columns_to_query string by validating each identifier
    if column == "*":
        columns_to_query = ", ".join(columns)
    else:
        # column validated already; ensure it is a safe identifier
        if not _is_valid_identifier(column):
            return "Invalid column name"
        columns_to_query = column

    # final safety: table and columns_to_query are validated; now construct query
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
    """Interactive paginated display of search results.

    - If allow_select is False (default) this function only displays pages and returns None.
    - If allow_select is True the user can enter a global result number to select an item; the
      function returns the selected integer index (1-based) or None if cancelled.
    """
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

        # If only one page and not selectable, just return
        if total_pages == 1 and not allow_select:
            return None

        # Navigation / selection prompt
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

        # prompt_with_back returns None when user pressed Enter or 'b'
        if choice is None:
            return None

        if choice.lower() == 'p' and current_page > 0:
            current_page -= 1
            continue
        if choice.lower() == 'n' and current_page < total_pages - 1:
            current_page += 1
            continue
        # At this point choice is not None and not a direct back; handle 'b' explicitly just in case
        if choice.lower() == 'b':
            return None
        if allow_select:
            try:
                sel = int(choice)
                if 1 <= sel <= total_items:
                    return sel
                else:
                    # clear before showing the invalid selection so the UI redraw is clean
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
            # unrecognized input when not selectable -> loop
            ui_clear()
            print('Invalid input')
            time.sleep(2)
            continue
