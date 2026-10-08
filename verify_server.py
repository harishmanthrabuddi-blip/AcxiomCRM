import urllib.request
import urllib.parse
import http.cookiejar
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. GET Login page
login_page = opener.open('http://127.0.0.1:5000/auth/login').read().decode('utf-8')
match = re.search(r'id="csrf_token"\s+name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', login_page)
if not match:
    match = re.search(r'value="([^"]+)"', login_page)

token = match.group(1)

# 2. POST Login credentials
post_data = urllib.parse.urlencode({
    'csrf_token': token,
    'email': 'admin@acxiom.com',
    'password': 'Admin@123'
}).encode('utf-8')

dashboard_res = opener.open('http://127.0.0.1:5000/auth/login', data=post_data).read().decode('utf-8')
print("1. Dashboard Login Verified:", "Executive Dashboard" in dashboard_res)

# 3. GET Customers List
cust_page = opener.open('http://127.0.0.1:5000/crm/customers').read().decode('utf-8')
print("2. Customers List Page Loaded:", "Acme Enterprises" in cust_page)

# 4. GET Leads List
leads_page = opener.open('http://127.0.0.1:5000/crm/leads').read().decode('utf-8')
print("3. Leads List Page Loaded:", "Wayne Enterprises" in leads_page)

# 5. GET Opportunities List
opps_page = opener.open('http://127.0.0.1:5000/crm/opportunities').read().decode('utf-8')
print("4. Opportunities Page Loaded:", "Acme Cloud ERP Migration" in opps_page)

# 6. GET Reports Hub
reports_page = opener.open('http://127.0.0.1:5000/reports/pipeline').read().decode('utf-8')
print("5. Pipeline Forecast Report Loaded:", "Sales Pipeline Forecast Report" in reports_page)
