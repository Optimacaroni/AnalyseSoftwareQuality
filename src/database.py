import sqlite3

Roles = ('system_admin', 'service_engineer')
Genders = ('Male', 'Female')
Cities = ('Rotterdam', 'Delft', 'Amsterdam', 'Groningen', 'Arnhem', 'Zwolle', 'Eindhoven', 'Den Haag', 'Utrecht', 'Maastricht')

def create_or_connect_db():
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    roles_str = str(Roles).replace('[', '(').replace(']', ')')

    cursor.execute(f"""CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username BLOB NOT NULL,
        password BLOB NOT NULL,
        first_name BLOB NOT NULL,
        last_name BLOB NOT NULL,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        role_level TEXT NOT NULL CHECK(role_level IN {roles_str})
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Travellers (
        customer_id TEXT PRIMARY KEY,
        first_name BLOB NOT NULL,
        last_name BLOB NOT NULL,
        birthday BLOB NOT NULL,
        gender BLOB NOT NULL,
        street_name BLOB NOT NULL,
        house_number BLOB NOT NULL,
        zip_code BLOB NOT NULL,
        city BLOB NOT NULL,
        email BLOB NOT NULL,
        mobile_phone BLOB NOT NULL,
        driving_license_number BLOB NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Scooters (
        scooter_id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand BLOB NOT NULL,
        model BLOB NOT NULL,
        serial_number BLOB NOT NULL,
        top_speed BLOB NOT NULL,
        battery_capacity BLOB NOT NULL,
        state_of_charge BLOB NOT NULL,
        target_range_min_soc BLOB NOT NULL,
        target_range_max_soc BLOB NOT NULL,
        latitude BLOB NOT NULL,
        longitude BLOB NOT NULL,
        out_of_service BLOB NOT NULL,
        mileage BLOB NOT NULL,
        last_maintenance_date BLOB NOT NULL,
        in_service_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS RestoreCodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        admin_user_id INTEGER NOT NULL,
        backup_filename TEXT NOT NULL,
        used INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_user_id) REFERENCES Users(id)
    )""")

    # Password recovery tokens table
    cursor.execute("""CREATE TABLE IF NOT EXISTS PasswordRecoveryTokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(id)
    )""")

    connection.commit()
    connection.close()

def clear_database():
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS RestoreCodes")
    cursor.execute("DROP TABLE IF EXISTS Scooters")
    cursor.execute("DROP TABLE IF EXISTS Travellers")
    cursor.execute("DROP TABLE IF EXISTS Users")

    connection.commit()
    connection.close()


# Schema whitelist for other modules to use (columns -> whether encrypted)
ALLOWED_COLUMNS = {
    "Users": {
        "username": True,
        "first_name": True,
        "last_name": True,
        "role_level": False
    },
    "Travellers": {
        "customer_id": False,
        "first_name": True,
        "last_name": True,
        "birthday": True,
        "gender": True,
        "street_name": True,
        "house_number": True,
        "zip_code": True,
        "city": True,
        "email": True,
        "mobile_phone": True,
        "driving_license_number": True
    },
    "Scooters": {
        "brand": True,
        "model": True,
        "serial_number": True,
        "top_speed": False,
        "battery_capacity": False,
        "state_of_charge": False,
        "target_range_min_soc": False,
        "target_range_max_soc": False,
        "latitude": False,
        "longitude": False,
        "out_of_service": False,
        "mileage": False,
        "last_maintenance_date": False
    }
}

# Type hints for non-encrypted columns to coerce/validate values
TYPE_MAP = {
    "Scooters": {
        "top_speed": float,
        "battery_capacity": int,
        "state_of_charge": int,
        "target_range_min_soc": int,
        "target_range_max_soc": int,
        "latitude": float,
        "longitude": float,
        "out_of_service": int,
        "mileage": float,
        "last_maintenance_date": "date"
    },
    "Travellers": {
        "house_number": int,
        "zip_code": str,
        "mobile_phone": str,
        "birthday": "date"
    },
    "Users": {
        "role_level": str
    }
}


from safe_data import encrypt_data, public_key
from safe_data import decrypt_data, private_key
import secrets
import hashlib
import datetime


def validate_and_prepare_value(table: str, column: str, new_data):
    """Validate and prepare a value for storage according to ALLOWED_COLUMNS and TYPE_MAP.

    Returns the prepared value (bytes for encrypted columns or coerced python type / string for others).
    Raises ValueError on invalid input.
    """
    # table/column existence
    if table not in ALLOWED_COLUMNS:
        raise ValueError("Invalid table specified for update")
    if column not in ALLOWED_COLUMNS[table]:
        raise ValueError("Invalid column specified for update")

    # Null-byte check
    if isinstance(new_data, str) and "\x00" in new_data:
        raise ValueError("Invalid input: null byte detected")

    # If column is encrypted, ensure it's a string and encrypt
    encrypt_flag = ALLOWED_COLUMNS[table][column]
    if encrypt_flag:
        # Accept ints/floats by converting to str first
        if not isinstance(new_data, str):
            new_data = str(new_data)
        try:
            return encrypt_data(public_key(), new_data)
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    # Non-encrypted: coerce based on TYPE_MAP if present
    if table in TYPE_MAP and column in TYPE_MAP[table]:
        expected = TYPE_MAP[table][column]
        if expected == "date":
            import datetime as _dt
            try:
                _dt.datetime.strptime(new_data, "%Y-%m-%d")
                return new_data
            except Exception:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
        elif expected is int:
            try:
                return int(new_data)
            except Exception:
                raise ValueError(f"Invalid integer value for {column}.")
        elif expected is float:
            try:
                return float(new_data)
            except Exception:
                raise ValueError(f"Invalid numeric value for {column}.")
        else:
            return str(new_data)

    # Default fallback: store as string
    return str(new_data)


def update_column(table: str, column: str, id_field: str, id_value, prepared_value) -> bool:
    """Safely update a single column in a table after validating identifiers.

    - Validates that table and column are in ALLOWED_COLUMNS.
    - Validates id_field is a safe identifier (basic regex).
    - Executes a parameterized UPDATE and returns True if rows were affected.
    """
    import re
    if table not in ALLOWED_COLUMNS:
        raise ValueError("Invalid table specified for update")
    if column not in ALLOWED_COLUMNS[table]:
        raise ValueError("Invalid column specified for update")

    # basic identifier check for id_field
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', id_field):
        raise ValueError("Invalid id field identifier")

    conn = sqlite3.connect("scooterfleet.db")
    cur = conn.cursor()
    sql = f"UPDATE {table} SET {column} = ? WHERE {id_field} = ?"
    cur.execute(sql, (prepared_value, id_value))
    conn.commit()
    rowcount = cur.rowcount
    conn.close()
    return rowcount > 0


def create_recovery_token_for_username(decrypted_username: str, validity_minutes: int = 15):
    """Create a recovery token for a user identified by decrypted username.

    Returns the plaintext token (to be delivered to the user) or None if user not found.
    """
    conn = sqlite3.connect("scooterfleet.db")
    cur = conn.cursor()
    # Find user id by decrypting usernames in the Users table
    cur.execute("SELECT id, username FROM Users")
    rows = cur.fetchall()
    target_id = None
    for rid, enc_uname in rows:
        try:
            if decrypt_data(private_key(), enc_uname).lower() == decrypted_username.lower():
                target_id = rid
                break
        except Exception:
            continue

    if target_id is None:
        conn.close()
        return None

    # generate token and store its hash
    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=validity_minutes)).isoformat()

    cur.execute("INSERT INTO PasswordRecoveryTokens (user_id, token_hash, expires_at, used) VALUES (?, ?, ?, 0)",
                (target_id, token_hash, expires_at))
    conn.commit()
    conn.close()
    return token


def verify_and_consume_recovery_token(decrypted_username: str, token: str) -> bool:
    """Verify a recovery token for the given decrypted username. If valid, mark it used and return True.
    Otherwise return False.
    """
    conn = sqlite3.connect("scooterfleet.db")
    cur = conn.cursor()
    # find user id
    cur.execute("SELECT id, username FROM Users")
    rows = cur.fetchall()
    target_id = None
    for rid, enc_uname in rows:
        try:
            if decrypt_data(private_key(), enc_uname).lower() == decrypted_username.lower():
                target_id = rid
                break
        except Exception:
            continue

    if target_id is None:
        conn.close()
        return False

    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("SELECT id FROM PasswordRecoveryTokens WHERE user_id = ? AND token_hash = ? AND used = 0 AND expires_at >= ?",
                (target_id, token_hash, now))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    token_id = row[0]
    cur.execute("UPDATE PasswordRecoveryTokens SET used = 1 WHERE id = ?", (token_id,))
    conn.commit()
    conn.close()
    return True
