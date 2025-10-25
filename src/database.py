import sqlite3

Roles = ('system_admin', 'service_engineer')
Genders = ('Male', 'Female')
Cities = ('Rotterdam', 'Delft', 'Schiedam', 'Vlaardingen', 'Capelle', 'Schipluiden', 'Maassluis', 'Barendrecht', 'Ridderkerk', 'Spijkenisse')

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
