from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import os

KEY_PATH = 'um.key'

def _load_or_create_key():
    if not os.path.exists(KEY_PATH):
        key = Fernet.generate_key()
        with open(KEY_PATH, 'wb') as f:
            f.write(key)
    else:
        with open(KEY_PATH, 'rb') as f:
            key = f.read()
    return key

# Backwards-compatible API names
def private_key():
    return _load_or_create_key()

def public_key():
    return _load_or_create_key()

def encrypt_data(key, data):
    # Accept str/int/float, store bytes
    if not isinstance(data, str):
        data = str(data)
    f = Fernet(key)
    return f.encrypt(data.encode('utf-8'))

def decrypt_data(key, encrypted_data):
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode('utf-8')
