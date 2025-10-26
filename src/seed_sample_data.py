"""Seed the scooterfleet.db with sample users, travellers and scooters.

This script is safe to run multiple times; it will create tables if missing and
insert sample rows if they don't already exist.

Run from project root (workspace `src`):
    python src/seed_sample_data.py

For deterministic encryption during seeding this script will set a temporary
UM_PASSPHRASE if none is present in the environment. In production you should
NOT hardcode secrets.
"""
import os
import sqlite3
import bcrypt
import datetime
import random

from database import create_or_connect_db, validate_and_prepare_value
from safe_data import encrypt_data, public_key


def ensure_passphrase_for_seeding():
    # Avoid interactive passphrase prompt when running seed script.
    if not os.environ.get('UM_PASSPHRASE') and not os.path.exists('um.salt') and not os.path.exists('um.key'):
        os.environ['UM_PASSPHRASE'] = 'SeedPass123!'


def insert_user(conn, username, password, role, first_name, last_name):
    cur = conn.cursor()
    # Note: caller should check existence; this function always inserts the provided user.

    enc_username = encrypt_data(public_key(), username)
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    enc_first = encrypt_data(public_key(), first_name)
    enc_last = encrypt_data(public_key(), last_name)
    cur.execute(
        "INSERT INTO Users (username, password, first_name, last_name, role_level) VALUES (?, ?, ?, ?, ?)",
        (enc_username, pw_hash, enc_first, enc_last, role),
    )


def insert_traveller(conn, data_dict):
    cur = conn.cursor()
    # prepare values via helper (handles encryption)
    cols = [
        'customer_id', 'first_name', 'last_name', 'birthday', 'gender', 'street_name',
        'house_number', 'zip_code', 'city', 'email', 'mobile_phone', 'driving_license_number'
    ]
    vals = []
    for col in cols:
        vals.append(validate_and_prepare_value('Travellers', col, data_dict[col]))

    cur.execute(
        "INSERT INTO Travellers (customer_id, first_name, last_name, birthday, gender, street_name, house_number, zip_code, city, email, mobile_phone, driving_license_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tuple(vals),
    )


def insert_scooter(conn, scooter):
    cur = conn.cursor()
    cols = [
        'brand', 'model', 'serial_number', 'top_speed', 'battery_capacity', 'state_of_charge',
        'target_range_min_soc', 'target_range_max_soc', 'latitude', 'longitude', 'out_of_service',
        'mileage', 'last_maintenance_date'
    ]
    vals = []
    for col in cols:
        vals.append(validate_and_prepare_value('Scooters', col, scooter[col]))

    cur.execute(
        "INSERT INTO Scooters (brand, model, serial_number, top_speed, battery_capacity, state_of_charge, target_range_min_soc, target_range_max_soc, latitude, longitude, out_of_service, mileage, last_maintenance_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tuple(vals),
    )


def generate_customer_id():
    current_date = str(datetime.datetime.now().year)
    customer_id = current_date[-2:]
    checksum = sum(int(d) for d in customer_id)
    for _ in range(7):
        rn = random.randint(0, 9)
        customer_id += str(rn)
        checksum += rn
    checksum %= 10
    customer_id += str(checksum)
    return customer_id


def main():
    ensure_passphrase_for_seeding()
    create_or_connect_db()
    conn = sqlite3.connect('scooterfleet.db')
    cur = conn.cursor()
    # Insert sample users if missing (check by decrypting stored usernames)
    def user_exists(username_to_check):
        cur.execute('SELECT username FROM Users')
        rows = cur.fetchall()
        for (enc_uname,) in rows:
            try:
                from safe_data import decrypt_data, private_key
                dec = decrypt_data(private_key(), enc_uname)
                if dec == username_to_check:
                    return True
            except Exception:
                continue
        return False

    users_to_ensure = [
        ('sys_admin', 'SystemAdmin_123!', 'system_admin', 'System', 'Admin'),
        ('eng_john', 'Engineer_123!', 'service_engineer', 'John', 'Doe')
    ]
    any_inserted = False
    for u in users_to_ensure:
        if not user_exists(u[0]):
            print(f"Inserting user {u[0]}...")
            insert_user(conn, *u)
            any_inserted = True
    if any_inserted:
        conn.commit()

    # Insert sample travellers if none
    cur.execute('SELECT COUNT(*) FROM Travellers')
    if cur.fetchone()[0] == 0:
        print('Inserting sample travellers...')
        t1 = {
            'customer_id': generate_customer_id(),
            'first_name': 'Alice',
            'last_name': 'Smith',
            'birthday': '1990-05-14',
            'gender': 'Female',
            'street_name': 'Baker Street',
            'house_number': 221,
            'zip_code': '3011AB',
            'city': 'Rotterdam',
            'email': 'alice.smith@example.com',
            'mobile_phone': '12345678',
            'driving_license_number': 'AB1234567'
        }
        insert_traveller(conn, t1)
        conn.commit()

    # Insert sample scooters
    cur.execute('SELECT COUNT(*) FROM Scooters')
    if cur.fetchone()[0] == 0:
        print('Inserting sample scooters...')
        s1 = {
            'brand': 'Segway',
            'model': 'Ninebot ES4',
            'serial_number': 'SN1234567890',
            'top_speed': 25,
            'battery_capacity': 374,
            'state_of_charge': 80,
            'target_range_min_soc': 20,
            'target_range_max_soc': 80,
            'latitude': 51.9225,
            'longitude': 4.47917,
            'out_of_service': 0,
            'mileage': 120.5,
            'last_maintenance_date': '2025-09-01'
        }
        insert_scooter(conn, s1)
        conn.commit()

    # Print counts
    cur.execute('SELECT COUNT(*) FROM Users')
    print('Users:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM Travellers')
    print('Travellers:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM Scooters')
    print('Scooters:', cur.fetchone()[0])

    conn.close()


if __name__ == '__main__':
    main()
