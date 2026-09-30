import base64
import os
from cryptography.fernet import Fernet
from flask import current_app

def get_cipher_suite(key=None):
    """Retrieve or construct a valid Fernet cipher instance."""
    if key is None:
        if current_app:
            key = current_app.config.get('ENCRYPTION_KEY')
        else:
            key = os.getenv('ENCRYPTION_KEY', 'c2VjdXJldmF1bHRfMzJfYnl0ZXNfa2V5XzAxMjM0NQ==')
    
    if isinstance(key, str):
        key_bytes = key.encode('utf-8')
    else:
        key_bytes = key
        
    try:
        return Fernet(key_bytes)
    except Exception as e:
        # Fallback to deterministic key deriving from string if raw base64 is malformed
        derived_key = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
        return Fernet(derived_key)

def encrypt_password(plain_password: str, key=None) -> str:
    """Encrypt plain text password string returning Fernet token string."""
    if not plain_password:
        return ""
    cipher = get_cipher_suite(key)
    encrypted_bytes = cipher.encrypt(plain_password.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_password(encrypted_password: str, key=None) -> str:
    """Decrypt Fernet token string returning original plain text password."""
    if not encrypted_password:
        return ""
    try:
        cipher = get_cipher_suite(key)
        decrypted_bytes = cipher.decrypt(encrypted_password.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        return "[Decryption Error]"
