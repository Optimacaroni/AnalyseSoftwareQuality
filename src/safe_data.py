import os
import base64
from getpass import getpass
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Files
KEY_PATH = 'um.key'    # legacy key file (kept for backward compatibility)
SALT_PATH = 'um.salt'  # salt file used for passphrase-derived key

# Internal cache
_cached_key = None


def _derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    # Use PBKDF2 to derive a 32-byte key then urlsafe_b64 encode for Fernet
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode('utf-8')))
    return key


def _load_legacy_keyfile():
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'rb') as f:
            return f.read()
    return None


def _load_or_create_salt():
    if os.path.exists(SALT_PATH):
        with open(SALT_PATH, 'rb') as f:
            return f.read()
    # create a new salt and store it (not secret)
    salt = os.urandom(16)
    with open(SALT_PATH, 'wb') as f:
        f.write(salt)
    return salt


def _get_key():
    """Return a Fernet-compatible base64 key (bytes).

    Behaviour:
    - If a salt file exists, derive the key from a passphrase (env UM_PASSPHRASE or prompt).
    - Else if legacy um.key file exists, use it for backward compatibility (warning).
    - Else prompt for a passphrase, create salt file and derive key.
    """
    global _cached_key
    if _cached_key is not None:
        return _cached_key

    # If salt exists, use passphrase-derived key
    if os.path.exists(SALT_PATH):
        salt = _load_or_create_salt()
        passphrase = os.environ.get('UM_PASSPHRASE')
        if not passphrase:
            # prompt the user for passphrase when first needed
            passphrase = getpass('Enter passphrase for data encryption/decryption: ')
        _cached_key = _derive_key_from_passphrase(passphrase, salt)
        return _cached_key

    # No salt file: check for legacy key file
    legacy = _load_legacy_keyfile()
    if legacy:
        # Use legacy key to preserve ability to read existing DB/logs
        # Warn the user that this key file is insecure and recommend migration
        try:
            print('Warning: using legacy key file (um.key). For better security, migrate to passphrase-derived key.')
        except Exception:
            pass
        _cached_key = legacy
        return _cached_key

    # No legacy keyfile either: create salt and derive from passphrase
    salt = _load_or_create_salt()
    passphrase = os.environ.get('UM_PASSPHRASE')
    if not passphrase:
        passphrase = getpass('Create a passphrase for data encryption: ')
    _cached_key = _derive_key_from_passphrase(passphrase, salt)
    return _cached_key


# Backwards-compatible API names
def private_key():
    return _get_key()


def public_key():
    return _get_key()


def encrypt_data(key, data):
    # Accept str/int/float, store bytes
    if not isinstance(data, str):
        data = str(data)
    f = Fernet(key)
    return f.encrypt(data.encode('utf-8'))


def decrypt_data(key, encrypted_data):
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode('utf-8')
