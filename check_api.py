import json
import urllib.request
import urllib.parse

# Login
data = urllib.parse.urlencode({
    'username': 'admin@sagarmatha.ai',
    'password': 'adadad123'
}).encode()

req = urllib.request.Request(
    'http://localhost:8000/api/v1/login/access-token',
    data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)

with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())['access_token']

# Get study
study_id = '521b4b98-87ec-4643-9103-eae78e2dad79'
req = urllib.request.Request(
    f'http://localhost:8000/api/v1/studies/{study_id}',
    headers={'Authorization': f'Bearer {token}'}
)

try:
    with urllib.request.urlopen(req) as response:
        study = json.loads(response.read().decode())
        # Check all keys
        print("Keys in study response:")
        for key in sorted(study.keys()):
            print(f"  - {key}")
        
        print(f"\ndashboard_template_id: {study.get('dashboard_template_id')}")
        
        # Check if it's in a different format
        if 'dashboardTemplateId' in study:
            print(f"dashboardTemplateId: {study.get('dashboardTemplateId')}")
            
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    if e.code == 500:
        print("Response:", e.read().decode())
