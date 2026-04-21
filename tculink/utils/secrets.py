import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Domain separation from other uses of SECRET_KEY (same pattern as Django signing salt).
_SMS_CREDENTIALS_KEY_CONTEXT = "opencarwings:sms_credentials:v1"


def sms_credentials_encryption_key_bytes():
    secret_key = getattr(settings, "SECRET_KEY", "") or ""
    if not str(secret_key).strip():
        raise ImproperlyConfigured("SECRET_KEY is required for SMS credential encryption")
    material = f"{_SMS_CREDENTIALS_KEY_CONTEXT}|{secret_key}"
    return hashlib.sha256(material.encode("utf-8")).digest()


def _get_encryption_key():
    return sms_credentials_encryption_key_bytes()


def encrypt_secret(value):
    if value is None:
        value = ""
    data = str(value).encode("utf-8")
    nonce = get_random_bytes(12)
    cipher = AES.new(_get_encryption_key(), AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return base64.b64encode(nonce + tag + ciphertext).decode("ascii")


def decrypt_secret(value):
    if not value:
        return ""
    payload = base64.b64decode(value.encode("ascii"))
    nonce = payload[:12]
    tag = payload[12:28]
    ciphertext = payload[28:]
    cipher = AES.new(_get_encryption_key(), AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8")
