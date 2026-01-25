import re

# Read app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Extract get_html function
match = re.search(r'def get_html\(\):\s+return """<!DOCTYPE html>.*?"""', app_content, re.DOTALL)
get_html_func = match.group(0)

# Read wsgi.py
with open('wsgi.py', 'r', encoding='utf-8') as f:
    wsgi_content = f.read()

# Replace get_html in wsgi.py
new_wsgi = re.sub(r'def get_html\(\):\s+return """<!DOCTYPE html>.*?"""', get_html_func, wsgi_content, count=1, flags=re.DOTALL)

# Write back
with open('wsgi.py', 'w', encoding='utf-8') as f:
    f.write(new_wsgi)

print('Synced')
