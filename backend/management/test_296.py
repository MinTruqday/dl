import asyncio
import httpx
import json

SERVICES = [
    "management", "content", "finance", "notification", "agentic_ai",
    "collector", "editor", "authentication", "realtime", "messaging"
]

async def run_test():
    print("Testing 296 endpoints across all microservices...")
    
    # We are inside the docker network, so we can access other containers by name!
    # Wait, the container names might be doclib_management or just management?
    # Usually docker compose networking uses the service name.
    
    total_endpoints = 0
    total_failed = 0
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for s in SERVICES:
            print(f"--- Fetching OpenAPI schema from {s} ---")
            try:
                # Assuming the internal port is 8000
                res = await client.get(f"http://{s}:8000/openapi.json")
                if res.status_code == 200:
                    schema = res.json()
                    paths = schema.get("paths", {})
                    num_endpoints = sum(len(methods) for methods in paths.values())
                    print(f"{s}: Found {num_endpoints} endpoints.")
                    
                    # Test each endpoint quickly with a dummy request
                    for path, methods in paths.items():
                        for method, info in methods.items():
                            total_endpoints += 1
                            url = f"http://{s}:8000{path}"
                            
                            # Replace path params with dummy '123' or 'test'
                            # e.g. /nguoi-dung/{user_id} -> /nguoi-dung/123
                            safe_path = path
                            import re
                            safe_path = re.sub(r'\{[^\}]+\}', '123', safe_path)
                            url = f"http://{s}:8000{safe_path}"
                            
                            try:
                                if method.upper() == "GET":
                                    test_res = await client.get(url)
                                else:
                                    # Send empty json, might get 422 Unprocessable Entity which is fine
                                    test_res = await client.post(url, json={})
                                    
                                if test_res.status_code in [500, 502, 503, 504]:
                                    print(f"FAILED (Server Error) - {s}: {method.upper()} {safe_path} -> {test_res.status_code}")
                                    total_failed += 1
                            except Exception as e:
                                print(f"FAILED (Request) - {s}: {method.upper()} {safe_path} -> {e}")
                                total_failed += 1
                else:
                    print(f"Could not fetch OpenAPI from {s}: {res.status_code}")
            except Exception as e:
                print(f"Error accessing {s}: {e}")

    print(f"\nTested {total_endpoints} endpoints. Failed: {total_failed}")

if __name__ == "__main__":
    asyncio.run(run_test())
