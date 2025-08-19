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

# Test study API
study_id = '521b4b98-87ec-4643-9103-eae78e2dad79'
print("Testing Dashboard APIs")
print("=" * 50)

# 1. Get study
req = urllib.request.Request(
    f'http://localhost:8000/api/v1/studies/{study_id}',
    headers={'Authorization': f'Bearer {token}'}
)

with urllib.request.urlopen(req) as response:
    study = json.loads(response.read().decode())
    print(f"Study: {study['name']}")
    print(f"Template ID: {study.get('dashboard_template_id')}")
    template_id = study.get('dashboard_template_id')

# 2. Get template
if template_id:
    req = urllib.request.Request(
        f'http://localhost:8000/api/v1/dashboard-templates/{template_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    with urllib.request.urlopen(req) as response:
        template = json.loads(response.read().decode())
        print(f"\nTemplate: {template['name']}")
        print(f"Template Structure Keys: {list(template.get('template_structure', {}).keys())}")
        
        if template.get('template_structure'):
            ts = template['template_structure']
            if 'dashboardTemplates' in ts:
                print(f"Dashboard Templates: {len(ts['dashboardTemplates'])}")
                for dt in ts['dashboardTemplates']:
                    print(f"  - {dt.get('name', 'Unnamed')}")
                    print(f"    Widgets: {len(dt.get('widgets', []))}")
