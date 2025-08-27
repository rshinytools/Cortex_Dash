from cryptography.fernet import Fernet
import base64

# Generate a proper Fernet key
key = Fernet.generate_key()
print("Raw key (bytes):", key)
print("Key length:", len(key))
print("\nUse this in docker-compose.yml:")
print(f"ENCRYPTION_KEY={key.decode()}")