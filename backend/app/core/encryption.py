# ABOUTME: Encryption utilities for sensitive data like SMTP passwords
# ABOUTME: Uses Fernet symmetric encryption for secure storage

from cryptography.fernet import Fernet
from typing import Optional
import base64
import os
from app.core.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        # Get or generate encryption key
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from settings or generate one"""
        # Try to get from environment variable
        key_str = os.getenv("ENCRYPTION_KEY")
        
        if key_str:
            # Decode from base64
            return base64.urlsafe_b64decode(key_str)
        else:
            # Generate a new key (should be stored securely in production)
            key = Fernet.generate_key()
            # Log warning in development
            print("WARNING: Using generated encryption key. Set ENCRYPTION_KEY env variable in production!")
            return key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded ciphertext"""
        if not plaintext:
            return ""
        
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64 encoded ciphertext and return plaintext"""
        if not ciphertext:
            return ""
        
        try:
            decoded = base64.urlsafe_b64decode(ciphertext)
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption failed: {str(e)}")
            return ""
    
    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(encrypted_data[field])
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        return decrypted_data


# Singleton instance
encryption_service = EncryptionService()