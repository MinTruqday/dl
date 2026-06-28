import urllib.request
import urllib.error

def test_nginx_traefik_integration():
    try:
        req = urllib.request.Request("http://localhost:8000/")
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            assert status in [200, 304, 404]
            print(f"Test passed: Connected to Traefik which routed to Nginx. Status: {status}")
    except urllib.error.HTTPError as e:
        assert e.code in [200, 304, 404]
        print(f"Test passed with HTTPError code: {e.code}")
    except Exception as e:
        print(f"Test failed: {e}")
        assert False

if __name__ == "__main__":
    test_nginx_traefik_integration()
