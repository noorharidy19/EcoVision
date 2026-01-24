import json
import urllib.request

url = 'http://127.0.0.1:8000/auth/signup'
# long password (200 chars)
data = {
    'full_name': 'Test User',
    'phone_number': '123',
    'email': 'longpw_test2@example.com',
    'password': 'p' * 200
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
try:
    resp = urllib.request.urlopen(req)
    print('STATUS', resp.status)
    print(resp.read().decode())
except Exception as e:
    import traceback
    traceback.print_exc()
