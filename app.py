#!/usr/bin/env python3
"""GTD Task Manager - Python Implementation"""
import json
import os
import hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import webbrowser
from http.cookies import SimpleCookie
import secrets

USERS_FILE = "users.json"
SESSIONS_FILE = "sessions.json"

def hash_password(password):
    """Hash a password using SHA256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + ':' + pwd_hash.hex()

def verify_password(password, hashed):
    """Verify a password against a hash"""
    if hashed is None:
        return False
    try:
        salt, pwd_hash = hashed.split(':')
        check_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwd_hash == check_hash.hex()
    except Exception as e:
        # If format is wrong, might be old plain text password
        print(f"Password verification error: {e}, hashed={hashed}")
        return False

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

sessions = load_sessions()  # session_id -> username

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        # Ensure admin account always exists
        if 'admin' not in users:
            users['admin'] = {"password": hash_password("admin"), "isAdmin": True}
            save_users(users)
        return users
    # Create default admin account
    default_users = {"admin": {"password": hash_password("admin"), "isAdmin": True}}
    save_users(default_users)
    return default_users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_data_file(username):
    return f"data_{username}.json"

def load_data(username):
    data_file = get_data_file(username)
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {"projects": [], "items": [], "nextProjectId": 1, "nextItemId": 1}

def save_data(username, data):
    data_file = get_data_file(username)
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)

class GTDHandler(BaseHTTPRequestHandler):
    def get_session_username(self):
        """Extract username from session cookie"""
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookie = SimpleCookie(cookie_header)
            if 'session_id' in cookie:
                session_id = cookie['session_id'].value
                return sessions.get(session_id)
        return None
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_html().encode())
        elif path == '/api/check-session':
            username = self.get_session_username()
            if username:
                users = load_users()
                is_admin = users.get(username, {}).get('isAdmin', False)
                self.send_json({"authenticated": True, "username": username, "isAdmin": is_admin})
            else:
                self.send_json({"authenticated": False})
        elif path == '/api/data':
            username = self.get_session_username()
            if not username:
                self.send_error(401, "Not authenticated")
                return
            data = load_data(username)
            self.send_json(data)
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        req_data = json.loads(body) if body else {}
        
        if path == '/api/login':
            username = req_data.get('username', '').strip()
            password = req_data.get('password', '')
            
            if not username:
                self.send_json({"success": False, "message": "Username required"})
                return
            
            users = load_users()
            
            # Check if user exists
            if username in users:
                # Check if user needs password reset
                if users[username].get('needsPasswordReset', False):
                    # User needs to set password - allow login with empty password
                    if password == '':
                        self.send_json({"success": True, "needsPasswordSetup": True, "username": username})
                    else:
                        self.send_json({"success": False, "message": "Please login with empty password to set your password"})
                    return
                
                # Normal login flow - password required for normal users
                if not password:
                    self.send_json({"success": False, "message": "Password required"})
                    return
                
                if verify_password(password, users[username]['password']):
                    # Successful login
                    session_id = secrets.token_hex(16)
                    sessions[session_id] = username
                    save_sessions(sessions)
                    
                    is_admin = users[username].get('isAdmin', False)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "username": username, "isAdmin": is_admin}).encode())
                else:
                    self.send_json({"success": False, "message": "Invalid password"})
            else:
                self.send_json({"success": False, "message": "Account does not exist"})
            return
        
        if path == '/api/logout':
            cookie_header = self.headers.get('Cookie')
            if cookie_header:
                cookie = SimpleCookie(cookie_header)
                if 'session_id' in cookie:
                    session_id = cookie['session_id'].value
                    sessions.pop(session_id, None)
                    save_sessions(sessions)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Set-Cookie', 'session_id=; Path=/; HttpOnly; Max-Age=0')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())
            return
        
        if path == '/api/admin/create-user':
            username = self.get_session_username()
            if not username:
                self.send_error(401, "Not authenticated")
                return
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                self.send_error(403, "Not authorized")
                return
            
            new_username = req_data.get('username', '').strip()
            
            if not new_username:
                self.send_json({"success": False, "message": "Username required"})
                return
            
            if new_username in users:
                self.send_json({"success": False, "message": "User already exists"})
                return
            
            users[new_username] = {"password": None, "isAdmin": False, "needsPasswordReset": True}
            save_users(users)
            self.send_json({"success": True, "message": f"User '{new_username}' created successfully"})
            return
        
        if path == '/api/admin/list-users':
            username = self.get_session_username()
            if not username:
                self.send_error(401, "Not authenticated")
                return
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                self.send_error(403, "Not authorized")
                return
            
            user_list = [{"username": u, "isAdmin": data.get('isAdmin', False)} for u, data in users.items()]
            self.send_json({"users": user_list})
            return
        
        if path == '/api/admin/delete-user':
            username = self.get_session_username()
            if not username:
                self.send_error(401, "Not authenticated")
                return
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                self.send_error(403, "Not authorized")
                return
            
            delete_username = req_data.get('username', '')
            
            if delete_username == 'admin':
                self.send_json({"success": False, "message": "Cannot delete admin account"})
                return
            
            if delete_username not in users:
                self.send_json({"success": False, "message": "User not found"})
                return
            
            del users[delete_username]
            save_users(users)
            
            # Delete user's data file
            data_file = get_data_file(delete_username)
            if os.path.exists(data_file):
                os.remove(data_file)
            
            self.send_json({"success": True, "message": f"User '{delete_username}' deleted"})
            return
        
        if path == '/api/admin/reset-password':
            username = self.get_session_username()
            if not username:
                self.send_error(401, "Not authenticated")
                return
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                self.send_error(403, "Not authorized")
                return
            
            reset_username = req_data.get('username', '')
            
            if reset_username not in users:
                self.send_json({"success": False, "message": "User not found"})
                return
            
            users[reset_username]['password'] = None
            users[reset_username]['needsPasswordReset'] = True
            save_users(users)
            self.send_json({"success": True, "message": f"Password reset for '{reset_username}'"})
            return
        
        if path == '/api/set-password':
            set_username = req_data.get('username', '').strip()
            new_password = req_data.get('password', '')
            
            if not set_username or not new_password:
                self.send_json({"success": False, "message": "Username and password required"})
                return
            
            users = load_users()
            
            if set_username not in users:
                self.send_json({"success": False, "message": "User not found"})
                return
            
            if not users[set_username].get('needsPasswordReset', False):
                self.send_json({"success": False, "message": "User does not need password reset"})
                return
            
            users[set_username]['password'] = hash_password(new_password)
            users[set_username]['needsPasswordReset'] = False
            save_users(users)
            
            # Create session for the user
            session_id = secrets.token_hex(16)
            sessions[session_id] = set_username
            save_sessions(sessions)
            
            is_admin = users[set_username].get('isAdmin', False)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "username": set_username, "isAdmin": is_admin}).encode())
            return
        
        username = self.get_session_username()
        if not username:
            self.send_error(401, "Not authenticated")
            return
        
        data = load_data(username)
        
        if path == '/api/items':
            item = {
                'title': req_data.get('title', ''),
                'notes': req_data.get('notes'),
                'status': req_data.get('status', 'inbox'),
                'projectId': req_data.get('projectId'),
                'startTime': req_data.get('startTime'),
                'dueDatetime': req_data.get('dueDatetime'),
                'position': req_data.get('position', 0),
                'id': data['nextItemId'],
                'createdAt': datetime.now().isoformat()
            }
            data['items'].append(item)
            data['nextItemId'] += 1
            save_data(username, data)
            self.send_json(item)
        elif path == '/api/projects':
            project = {
                'name': req_data.get('name', ''),
                'outcome': req_data.get('outcome'),
                'status': req_data.get('status', 'active'),
                'id': data['nextProjectId'],
                'createdAt': datetime.now().isoformat()
            }
            data['projects'].append(project)
            data['nextProjectId'] += 1
            save_data(username, data)
            self.send_json(project)
        else:
            self.send_error(404)
    
    def do_PUT(self):
        path = urlparse(self.path).path
        parts = path.split('/')
        
        username = self.get_session_username()
        if not username:
            self.send_error(401, "Not authenticated")
            return
            
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        updates = json.loads(body) if body else {}
        
        data = load_data(username)
        
        # Batch update endpoint for multiple items
        if path == '/api/items/batch':
            if not isinstance(updates, list):
                self.send_error(400, "Expected array of updates")
                return
            
            updated_count = 0
            for update in updates:
                item_id = update.get('id')
                if not item_id:
                    continue
                for i, item in enumerate(data['items']):
                    if item['id'] == item_id:
                        # Remove 'id' from updates to avoid overwriting
                        item_updates = {k: v for k, v in update.items() if k != 'id'}
                        data['items'][i].update(item_updates)
                        updated_count += 1
                        break
            
            save_data(username, data)
            self.send_json({"updated": updated_count})
            return
        
        if len(parts) < 4:
            self.send_error(400)
            return
        
        item_id = int(parts[3])
        
        if parts[2] == 'items':
            for i, item in enumerate(data['items']):
                if item['id'] == item_id:
                    data['items'][i].update(updates)
                    save_data(username, data)
                    self.send_json(data['items'][i])
                    return
        elif parts[2] == 'projects':
            for i, project in enumerate(data['projects']):
                if project['id'] == item_id:
                    data['projects'][i].update(updates)
                    save_data(username, data)
                    self.send_json(data['projects'][i])
                    return
        
        self.send_error(404)
    
    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = path.split('/')
        
        if len(parts) < 4:
            self.send_error(400)
            return
        
        username = self.get_session_username()
        if not username:
            self.send_error(401, "Not authenticated")
            return
            
        data = load_data(username)
        item_id = int(parts[3])
        
        if parts[2] == 'items':
            data['items'] = [i for i in data['items'] if i['id'] != item_id]
            save_data(username, data)
            self.send_response(204)
            self.end_headers()
        elif parts[2] == 'projects':
            data['projects'] = [p for p in data['projects'] if p['id'] != item_id]
            # Remove project reference from items
            for item in data['items']:
                if item.get('projectId') == item_id:
                    item['projectId'] = None
                    item['status'] = 'inbox'
            save_data(username, data)
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)
    
    def send_json(self, obj):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logging

def get_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == '__main__':
    PORT = 8000
    server = HTTPServer(('localhost', PORT), GTDHandler)
    print(f"\n✅ GTD Task Manager running at http://localhost:{PORT}")
    print(f"📁 User data saved to: data_<username>.json")
    print(f"\nPress Ctrl+C to stop\n")
    
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
