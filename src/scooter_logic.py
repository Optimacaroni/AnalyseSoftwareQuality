import sqlite3
import time
from safe_data import *
from validation import *
from log_config import logmanager as log_manager
from search import display_search_results, search
import database
from acl import require_role
from ui_helpers import clear as ui_clear, prompt_with_back

log_instance = log_manager()


def _encrypt(v):
    return encrypt_data(public_key(), v)


def _prompt(prompt, validator=None, transform=None, allow_empty=False):
    while True:
        v = input(prompt).strip()
        if allow_empty and v == "":
            return None
        if transform:
            try:
                tv = transform(v)
            except Exception:
                print("Invalid input format")
                continue
        else:
            tv = v
        if validator is None or validator(tv):
            return tv
        else:
            print("Invalid input")


@require_role('system_admin')
def add_scooter(username):
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()

    print("\n--- Add Scooter ---")
    brand = _prompt("Brand: ", lambda s: 1 <= len(s) <= 50)
    model = _prompt("Model: ", lambda s: 1 <= len(s) <= 50)
    serial = _prompt("Serial number (10-17 alnum): ", lambda s: bool(__import__('re').match(r'^[A-Za-z0-9]{10,17}$', s)))
    top_speed = _prompt("Top speed (km/h): ", lambda x: float(x) > 0, transform=float)
    battery_capacity = _prompt("Battery capacity (Wh): ", lambda x: int(x) > 0, transform=int)
    soc = _prompt("State of charge (0-100): ", lambda x: 0 <= int(x) <= 100, transform=int)
    target_min = _prompt("Target-range min SoC (0-100): ", lambda x: 0 <= int(x) <= 100, transform=int)
    target_max = _prompt("Target-range max SoC (0-100): ", lambda x: 0 <= int(x) <= 100, transform=int)
    latitude = _prompt("Latitude (e.g. 51.92250): ", lambda x: -90.0 <= float(x) <= 90.0, transform=float)
    longitude = _prompt("Longitude (e.g. 4.47917): ", lambda x: -180.0 <= float(x) <= 180.0, transform=float)
    out_of_service = _prompt("Out of service? (y/n): ", lambda x: x.lower() in ("y", "n")).lower()
    mileage = _prompt("Mileage (km): ", lambda x: float(x) >= 0, transform=float)
    last_maintenance = _prompt("Last maintenance date (YYYY-MM-DD): ", lambda x: __import__('datetime').datetime.strptime(x, "%Y-%m-%d"), transform=str)

    # Prepare fields using centralized validation/prepare helper
    data = (
        database.validate_and_prepare_value('Scooters', 'brand', brand),
        database.validate_and_prepare_value('Scooters', 'model', model),
        database.validate_and_prepare_value('Scooters', 'serial_number', serial),
        database.validate_and_prepare_value('Scooters', 'top_speed', str(top_speed)),
        database.validate_and_prepare_value('Scooters', 'battery_capacity', str(battery_capacity)),
        database.validate_and_prepare_value('Scooters', 'state_of_charge', str(soc)),
        database.validate_and_prepare_value('Scooters', 'target_range_min_soc', str(target_min)),
        database.validate_and_prepare_value('Scooters', 'target_range_max_soc', str(target_max)),
        database.validate_and_prepare_value('Scooters', 'latitude', str(latitude)),
        database.validate_and_prepare_value('Scooters', 'longitude', str(longitude)),
        database.validate_and_prepare_value('Scooters', 'out_of_service', "1" if out_of_service == "y" else "0"),
        database.validate_and_prepare_value('Scooters', 'mileage', str(mileage)),
        database.validate_and_prepare_value('Scooters', 'last_maintenance_date', last_maintenance)
    )

    cursor.execute(
        """
        INSERT INTO Scooters (
            brand, model, serial_number, top_speed, battery_capacity, state_of_charge,
            target_range_min_soc, target_range_max_soc, latitude, longitude, out_of_service,
            mileage, last_maintenance_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data
    )
    connection.commit()
    connection.close()
    print("Scooter added successfully")
    log_instance.log_activity(username, "Add scooter", f"Added scooter serial: {serial}", "No")
    time.sleep(1)


@require_role('service_engineer')
def modify_scooter(username, role):
    print("\n--- Modify Scooter ---")
    term = input("Enter search term: ").strip()
    results = search(term, "Scooters")
    if not results:
        print("No scooters found")
        time.sleep(1)
        return
    choice = display_search_results(results, show_numbers=True, allow_select=True)
    if choice is None:
        return
    if choice < 1 or choice > len(results)-1:
        ui_clear()
        print("Invalid choice")
        return
    selected = results[choice]
    scooter_id = selected[0]

    # Determine editable fields
    all_fields = {
        "1": ("brand", lambda v: 1 <= len(v) <= 50),
        "2": ("model", lambda v: 1 <= len(v) <= 50),
        "3": ("serial_number", lambda v: bool(__import__('re').match(r'^[A-Za-z0-9]{10,17}$', v))),
        "4": ("top_speed", lambda v: float(v) > 0),
        "5": ("battery_capacity", lambda v: int(v) > 0),
        "6": ("state_of_charge", lambda v: 0 <= int(v) <= 100),
        "7": ("target_range_min_soc", lambda v: 0 <= int(v) <= 100),
        "8": ("target_range_max_soc", lambda v: 0 <= int(v) <= 100),
        "9": ("latitude", lambda v: -90.0 <= float(v) <= 90.0),
        "10": ("longitude", lambda v: -180.0 <= float(v) <= 180.0),
        "11": ("out_of_service", lambda v: v.lower() in ("y", "n")),
        "12": ("mileage", lambda v: float(v) >= 0),
        "13": ("last_maintenance_date", lambda v: __import__('datetime').datetime.strptime(v, "%Y-%m-%d"))
    }

    # Service engineers are restricted: allow only fields 6-13
    if role == "service_engineer":
        editable_keys = [str(i) for i in range(6, 14)]
    else:
        editable_keys = list(all_fields.keys())

    print("Choose field to modify:")
    for k in editable_keys:
        print(f"{k}. {all_fields[k][0]}")
    sel = prompt_with_back("Field number: ")
    if sel is None:
        return
    if sel not in editable_keys:
        ui_clear()
        print("Invalid choice")
        return

    field_name, validator = all_fields[sel]
    new_value = input(f"Enter new value for {field_name}: ").strip()
    # Validate
    try:
        if not validator(new_value):
            print("Invalid value")
            return
    except Exception:
        print("Invalid value")
        return

    enc = _encrypt(str(new_value) if sel != "13" else new_value)
    # Use centralized safe updater to validate identifiers and run parameterized SQL
    try:
        ok = database.update_column('Scooters', field_name, 'scooter_id', scooter_id, enc)
        if not ok:
            print("No rows updated")
            return
    except Exception as e:
        print(f"Update failed: {e}")
        return
    print("Scooter updated successfully")
    log_instance.log_activity(username, "Modify scooter", f"Updated {field_name} of scooter id: {scooter_id}", "No")
    time.sleep(1)


@require_role('system_admin')
def delete_scooter(username):
    print("\n--- Delete Scooter ---")
    term = input("Enter search term: ").strip()
    results = search(term, "Scooters")
    if not results:
        print("No scooters found")
        time.sleep(1)
        return
    choice = display_search_results(results, show_numbers=True, allow_select=True)
    if choice is None:
        return
    if choice < 1 or choice > len(results)-1:
        ui_clear()
        print("Invalid choice")
        return
    selected = results[choice]
    scooter_id = selected[0]
    confirm = input("Are you sure you want to delete this scooter? (y/n): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Delete cancelled")
        return
    connection = sqlite3.connect("scooterfleet.db")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM Scooters WHERE scooter_id = ?", (scooter_id,))
    connection.commit()
    connection.close()
    print("Scooter deleted")
    log_instance.log_activity(username, "Delete scooter", f"Deleted scooter id: {scooter_id}", "No")
    time.sleep(1)
