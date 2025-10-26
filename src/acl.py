import sqlite3
from functools import wraps
import inspect
from safe_data import decrypt_data, private_key
from log_config import logmanager as log_manager

log_instance = log_manager()

# Role hierarchy (higher number = more privileges)
ROLE_RANK = {
    'service_engineer': 1,
    'system_admin': 2,
    'super_admin': 3
}


def _role_rank(role_name: str) -> int:
    return ROLE_RANK.get(role_name, 0)


def _get_role_for_username(username: str):
    # Hard-coded super admin
    if username == 'super_admin':
        return 'super_admin'

    conn = sqlite3.connect('scooterfleet.db')
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, username, role_level FROM Users')
        rows = cur.fetchall()
        for _id, enc_uname, role in rows:
            try:
                dec = decrypt_data(private_key(), enc_uname)
            except Exception:
                continue
            if dec == username:
                return role
    finally:
        conn.close()
    return None


def require_role(min_role: str):
    """Decorator to require at least min_role to call the function.

    The decorated function must accept `username` as the first positional
    argument or as a keyword argument named 'username'.
    """

    def decorator(f):
        sig = inspect.signature(f)

        @wraps(f)
        def wrapper(*args, **kwargs):
            # Try to get the username from bound arguments (supports positional or keyword args)
            try:
                bound = sig.bind_partial(*args, **kwargs)
            except Exception:
                bound = None

            username = None
            if bound:
                username = bound.arguments.get('username')

            # Fallback: if still missing, accept first positional argument as username (legacy behavior)
            if not username and len(args) > 0:
                username = args[0]
            if not username:
                print('Access denied: missing username')
                log_instance.log_activity('Unknown', 'Authorization', 'Missing username for protected action', 'Yes')
                return None

            role = _get_role_for_username(username)
            if not role:
                print('Access denied: user not found or not authorized')
                log_instance.log_activity(username, 'Authorization', 'User not found for role check', 'Yes')
                return None

            if _role_rank(role) < _role_rank(min_role):
                print('Access denied: insufficient privileges')
                log_instance.log_activity(username, 'Authorization', f'Insufficient privileges (needs {min_role}, has {role})', 'Yes')
                return None

            # allowed
            return f(*args, **kwargs)

        return wrapper

    return decorator
