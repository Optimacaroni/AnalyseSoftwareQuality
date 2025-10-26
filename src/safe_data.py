import os
import base64
from getpass import getpass
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Files
KEY_PATH = 'um.key'    
SALT_PATH = 'um.salt'  

# Internal cache
_cached_key = None


def _derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
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
    salt = os.urandom(16)
    with open(SALT_PATH, 'wb') as f:
        f.write(salt)
    return salt


def _get_key():
    global _cached_key
    if _cached_key is not None:
        return _cached_key

    if os.path.exists(SALT_PATH):
        salt = _load_or_create_salt()
        passphrase = os.environ.get('UM_PASSPHRASE')
        if not passphrase:
            passphrase = getpass('Enter passphrase for data encryption/decryption: ')
        _cached_key = _derive_key_from_passphrase(passphrase, salt)
        return _cached_key

    legacy = _load_legacy_keyfile()
    if legacy:
        allow_legacy = os.environ.get('ALLOW_LEGACY_KEY', '')
        if allow_legacy.lower() in ('1', 'true', 'yes'):
            try:
                print('WARNING: using legacy key file (um.key) because ALLOW_LEGACY_KEY is set. This is insecure; migrate to a passphrase-derived key ASAP.')
            except Exception:
                pass
            _cached_key = legacy
            return _cached_key
        raise RuntimeError(
            "Legacy key file 'um.key' found but not allowed.\n"
            "For security we require a passphrase-derived key.\n"
            "Options:\n"
            "  1) Set UM_PASSPHRASE to an encryption passphrase and restart (recommended).\n"
            "  2) To perform a one-time migration or allow legacy behavior temporarily, set ALLOW_LEGACY_KEY=1 (NOT RECOMMENDED).\n"
            "If you have backed up the original key file, move it out of the repository and follow the migration steps in MIGRATE.md.\n"
        )

    salt = _load_or_create_salt()
    passphrase = os.environ.get('UM_PASSPHRASE')
    if not passphrase:
        passphrase = getpass('Create a passphrase for data encryption: ')
    _cached_key = _derive_key_from_passphrase(passphrase, salt)
    return _cached_key


def private_key():
    return _get_key()


def public_key():
    return _get_key()


def encrypt_data(key, data):
    if not isinstance(data, str):
        data = str(data)
    f = Fernet(key)
    return f.encrypt(data.encode('utf-8'))


def decrypt_data(key, encrypted_data):
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode('utf-8')
