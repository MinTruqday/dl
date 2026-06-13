import os
import glob
import re
import requests
import json

def extract_api_paths():
    paths = set()
    service_files = glob.glob('frontend/**/services/*.ts', recursive=True)
    
    # Regex to find paths like `${API_URL}/path`
    pattern = re.compile(r'\$\{API_URL\}(/[^`"\'?$\\]+)')
    
    for file in service_files:
        with open(file, 'r') as f:
            content = f.read()
            matches = pattern.findall(content)
            for match in matches:
                # clean up variables like /path/${id} -> /path/123
                clean_path = re.sub(r'\$\{[^}]+\}', 'test_id', match)
                # also clean up + variable
                clean_path = clean_path.split('${')[0]
                if clean_path.endswith('/'):
                    clean_path = clean_path[:-1]
                if clean_path:
                    paths.add(clean_path)
    return sorted(list(paths))

def test_paths(paths):
    print(f"Found {len(paths)} unique API paths. Testing connections to localhost:8000...")
    
    issues = []
    
    for path in paths:
        url = f"http://localhost:8000{path}"
        try:
            # We do an OPTIONS request first, if not allowed we do GET
            # Actually, just a GET or POST. Let's do GET. It might return 405 Method Not Allowed, 
            # which is FINE because it means the route EXISTS.
            res = requests.get(url, timeout=3)
            status = res.status_code
        except Exception as e:
            issues.append((path, f"Connection Failed: {str(e)}"))
            continue
            
        if status == 404:
            # Let's try POST if GET is 404, just in case
            try:
                res2 = requests.post(url, timeout=3)
                if res2.status_code != 404:
                    status = res2.status_code
            except:
                pass
                
        # 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity, 405 Method Not Allowed, 200 OK -> Route is working!
        # 404 Not Found -> Route is missing!
        # 500 Internal Error -> Backend code crashed!
        # 502 Bad Gateway -> Service container is dead or Traefik can't route!
        if status in [404, 500, 502, 503, 504]:
            issues.append((path, f"HTTP {status}"))
        else:
            print(f"[OK] {path} -> {status}")
            
    print("\n" + "="*40)
    print("TEST RESULTS - FOUND ISSUES:")
    print("="*40)
    if not issues:
        print("Mọi API đều đã được kết nối thông suốt! Không có lỗi 404 hay 502 nào.")
    else:
        for path, error in issues:
            print(f"[ERROR] {path}: {error}")
            
if __name__ == "__main__":
    paths = extract_api_paths()
    test_paths(paths)
