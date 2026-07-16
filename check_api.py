import requests

url = "http://127.0.0.1:8000/api/alerts"
print(f"GET {url}")
try:
    res = requests.get(url, timeout=5)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}")
except Exception as e:
    print(f"Error: {e}")
