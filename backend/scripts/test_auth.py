import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.security import get_password_hash, verify_password

def test_hashing():
    password = "test@123"
    hashed = get_password_hash(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    
    is_valid = verify_password(password, hashed)
    print(f"Verification result: {is_valid}")

if __name__ == "__main__":
    test_hashing()
