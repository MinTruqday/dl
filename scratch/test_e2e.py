import requests
import time
import sys

BASE_URLS = {
    "identity": "http://localhost:8500",
    "administration": "http://localhost:8050",
    "billing": "http://localhost:8350",
    "documents": "http://localhost:8450",
    "workspace": "http://localhost:8300",
    "conversations": "http://localhost:8100",
    "alerts": "http://localhost:8150",
    "live_events": "http://localhost:8200",
    "ingestion": "http://localhost:8250",
    "task_queue": "http://localhost:8000" # wait, worker might not have port, it's a celery worker
}

def test_service(name, url):
    if name == "task_queue":
        return True # celery worker doesn't have an HTTP API exposed
    print(f"Testing {name} at {url}...")
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} (/health) - OK")
            return True
            
        response = requests.get(f"{url}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} (/docs) - OK")
            return True
            
        print(f"❌ {name} returned status code {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return False

def test_identity_register_and_login():
    print("Testing Identity Register...")
    url_reg = f"{BASE_URLS['identity']}/api/v1/auth/register"
    data_reg = {
        "email": "admin@doclib.com",
        "password": "123456",
        "full_name": "System Admin"
    }
    try:
        res = requests.post(url_reg, json=data_reg, timeout=5)
        if res.status_code in [200, 201]:
            print("✅ Identity Register OK")
        elif res.status_code == 400 and "already exists" in res.text:
            print("✅ Identity Register (User exists)")
        else:
            print(f"❌ Identity Register failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Identity Register error: {e}")

    print("Testing Identity Login...")
    url_login = f"{BASE_URLS['identity']}/api/v1/auth/login"
    data_login = {
        "username": "admin@doclib.com",
        "password": "123456"
    }
    try:
        res = requests.post(url_login, data=data_login, timeout=5)
        if res.status_code == 200:
            token = res.json().get("access_token")
            print("✅ Identity Login OK")
            return token
        else:
            print(f"❌ Identity Login failed: {res.status_code} {res.text}")
            return None
    except Exception as e:
        print(f"❌ Identity Login error: {e}")
        return None

def main():
    print("Starting E2E sequential testing...\n")
    all_passed = True
    for name, url in BASE_URLS.items():
        if not test_service(name, url):
            all_passed = False
            
    print("\n--- Deep Dive Testing ---")
    token = test_identity_register_and_login()
    if not token:
        all_passed = False
    
    if all_passed:
        print("\nAll tests passed successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
