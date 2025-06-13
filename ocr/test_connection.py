import requests
import time

FLASK_SERVER_URL = "https://a0c0-2402-3a80-45fe-b532-2cf7-63f1-433b-bb98.ngrok-free.app"

def test_endpoint(endpoint, method="GET", json_data=None):
    try:
        url = f"{FLASK_SERVER_URL}{endpoint}"
        print(f"\nTesting {method} {endpoint}")
        
        start_time = time.time()
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(
                url,
                json=json_data or {},
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
        
        elapsed = (time.time() - start_time) * 1000
        print(f"Status: {response.status_code} | Time: {elapsed:.2f}ms")
        
        try:
            print(f"Response: {response.json()}")
            return True
        except ValueError:
            print(f"Response (non-JSON): {response.text[:200]}...")
            return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")
        return False

def full_server_test():
    print("=== Starting Comprehensive Server Test ===")
    
    # First verify basic connectivity
    if not test_endpoint("/health"):
        print("\n❌ Failed basic health check")
        return False
    
    # Test all critical endpoints
    endpoints = [
        ("/", "GET"),
        ("/submit_complaint", "POST", {
            "chat_id": 12345,
            "problem": "AC not cooling",
            "address": "123 Test Street, Pune",
            "contact_no": "9876543210",
            "error_code": "E12",
            "media_path": ""
        })
    ]
    
    all_success = True
    for endpoint in endpoints:
        if not test_endpoint(*endpoint):
            all_success = False
    
    return all_success

if __name__ == "__main__":
    if full_server_test():
        print("\n✅ All endpoints working correctly!")
    else:
        print("\n❌ Some endpoints failed. Check your Flask application.")
        print("\nDebug Checklist:")
        print("1. Is Flask running? Check terminal for output")
        print("2. Does ngrok URL match FLASK_SERVER_URL?")
        print("3. Are there any errors in the Flask console?")
        print("4. Try accessing /health directly in browser")
