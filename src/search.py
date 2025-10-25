import sqlite3
import re
from safe_data import *

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

def display_search_results(search_results, show_numbers=True):
    print("--- Results ---")
    if type(search_results) == str:
        print(search_results)
        return
    if not search_results or len(search_results) == 0:
        print("No results.")
        return

    header_cols = search_results[0][:4] if len(search_results[0]) >= 4 else search_results[0]
    header = ("     " if show_numbers else "") + "".join(c.ljust(20) for c in header_cols)
    print(header)
    print("-" * len(header))

    for i, result in enumerate(search_results[1:], start=1):
        cols = result[:len(header_cols)]
        line = (f"[{i}]  " if show_numbers else "") + "".join(str(c).ljust(20) for c in cols)
        print(line)
