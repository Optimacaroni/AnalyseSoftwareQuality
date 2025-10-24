import sqlite3
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

def search(search_term, table, column="*", role=None):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    table = table.upper()
    cursor.execute(f"PRAGMA table_info({table})")
    columns_info = cursor.fetchall()
    columns = [info[1] for info in columns_info if "password" not in info[1].lower()]

    if not columns:
        return f"No columns found in {table}"

    if column != "*":
        column = column if column in columns else "*"

    columns_to_query = ", ".join(columns) if column == "*" else column

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
