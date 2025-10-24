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
