import base64
import hashlib
import json
from typing import Any
from cryptography.fernet import Fernet
from config import settings

def _get_fernet_instance() -> Fernet:
    """
    Derives a consistent 32-byte key from SECRET_KEY using SHA-256
    and returns a Fernet instance.
    
    Note: Fernet uses AES-128-CBC with HMAC-SHA256 for authenticated encryption.
    The 256-bit SHA-256 derived key is split: 128 bits for AES, 128 bits for HMAC.
    This provides strong authenticated encryption suitable for exam data at rest.
    """
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

_fernet = _get_fernet_instance()

def encrypt_text(plain_text: str) -> str:
    """Encrypt plaintext string using Fernet authenticated encryption (AES-128-CBC + HMAC-SHA256)"""
    if plain_text is None:
        return None
    encrypted_bytes = _fernet.encrypt(plain_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_text(cipher_text: str) -> str:
    """Decrypt Fernet ciphertext string back to plaintext"""
    if cipher_text is None:
        return None
    try:
        decrypted_bytes = _fernet.decrypt(cipher_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def encrypt_json(data: Any) -> str:
    """Serialize object to JSON and encrypt with Fernet"""
    if data is None:
        return None
    json_str = json.dumps(data)
    return encrypt_text(json_str)

def decrypt_json(cipher_text: str) -> Any:
    """Decrypt Fernet ciphertext and parse JSON object"""
    if cipher_text is None:
        return None
    json_str = decrypt_text(cipher_text)
    return json.loads(json_str)
