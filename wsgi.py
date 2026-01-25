#!/usr/bin/env python3
"""WSGI adapter for PythonAnywhere deployment"""
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie
import secrets

USERS_FILE = "users.json"
sessions = {}  # session_id -> username

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        if 'admin' not in users:
            users['admin'] = {"password": "admin", "isAdmin": True}
            save_users(users)
        return users
    default_users = {"admin": {"password": "admin", "isAdmin": True}}
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

def get_session_username(environ):
    """Extract username from session cookie"""
    cookie_header = environ.get('HTTP_COOKIE', '')
    if cookie_header:
        cookie = SimpleCookie(cookie_header)
        if 'session_id' in cookie:
            session_id = cookie['session_id'].value
            return sessions.get(session_id)
    return None

def get_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()



def application(environ, start_response):
    """WSGI application entry point"""
    method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    
    # Handle GET requests
    if method == 'GET':
        if path == '/':
            status = '200 OK'
            headers = [('Content-type', 'text/html')]
            start_response(status, headers)
            return [get_html().encode('utf-8')]
        
        elif path == '/api/check-session':
            username = get_session_username(environ)
            if username:
                users = load_users()
                is_admin = users.get(username, {}).get('isAdmin', False)
                response = {"authenticated": True, "username": username, "isAdmin": is_admin}
            else:
                response = {"authenticated": False}
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(response).encode('utf-8')]
        
        elif path == '/api/data':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            data = load_data(username)
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(data).encode('utf-8')]
        
        elif path == '/api/admin/users':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                status = '403 Forbidden'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Admin access required"}).encode('utf-8')]
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(users).encode('utf-8')]
    
    # Handle POST requests
    elif method == 'POST':
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        body = environ['wsgi.input'].read(content_length)
        req_data = json.loads(body) if body else {}
        
        if path == '/api/login':
            username = req_data.get('username', '').strip()
            password = req_data.get('password', '')
            
            if not username or not password:
                response = {"success": False, "message": "Username and password required"}
            else:
                users = load_users()
                if username in users and users[username]['password'] == password:
                    session_id = secrets.token_hex(16)
                    sessions[session_id] = username
                    
                    is_admin = users[username].get('isAdmin', False)
                    
                    status = '200 OK'
                    cookie = SimpleCookie()
                    cookie['session_id'] = session_id
                    cookie['session_id']['path'] = '/'
                    cookie['session_id']['max-age'] = 86400  # 24 hours
                    
                    headers = [
                        ('Content-type', 'application/json'),
                        ('Set-Cookie', cookie['session_id'].OutputString())
                    ]
                    start_response(status, headers)
                    return [json.dumps({"success": True, "username": username, "isAdmin": is_admin}).encode('utf-8')]
                else:
                    response = {"success": False, "message": "Invalid credentials"}
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(response).encode('utf-8')]
        
        elif path == '/api/logout':
            cookie_header = environ.get('HTTP_COOKIE', '')
            if cookie_header:
                cookie = SimpleCookie(cookie_header)
                if 'session_id' in cookie:
                    session_id = cookie['session_id'].value
                    sessions.pop(session_id, None)
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps({"success": True}).encode('utf-8')]
        
        elif path == '/api/data':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            save_data(username, req_data)
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps({"success": True}).encode('utf-8')]
        
        elif path == '/api/admin/create-user':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                status = '403 Forbidden'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Admin access required"}).encode('utf-8')]
            
            new_username = req_data.get('username', '').strip()
            new_password = req_data.get('password', '')
            is_admin = req_data.get('isAdmin', False)
            
            if not new_username or not new_password:
                response = {"success": False, "message": "Username and password required"}
            elif new_username in users:
                response = {"success": False, "message": "Username already exists"}
            else:
                users[new_username] = {"password": new_password, "isAdmin": is_admin}
                save_users(users)
                response = {"success": True, "message": f"User '{new_username}' created successfully"}
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(response).encode('utf-8')]
        
        elif path == '/api/admin/list-users':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                status = '403 Forbidden'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Admin access required"}).encode('utf-8')]
            
            user_list = [{"username": u, "isAdmin": data.get('isAdmin', False)} for u, data in users.items()]
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps({"users": user_list}).encode('utf-8')]
        
        elif path == '/api/admin/delete-user':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            users = load_users()
            if not users.get(username, {}).get('isAdmin', False):
                status = '403 Forbidden'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Admin access required"}).encode('utf-8')]
            
            delete_username = req_data.get('username', '').strip()
            
            if delete_username == 'admin':
                response = {"success": False, "message": "Cannot delete admin account"}
            elif delete_username not in users:
                response = {"success": False, "message": "User not found"}
            else:
                users.pop(delete_username)
                save_users(users)
                
                # Delete user's data file
                data_file = get_data_file(delete_username)
                if os.path.exists(data_file):
                    os.remove(data_file)
                
                response = {"success": True, "message": f"User '{delete_username}' deleted"}
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(response).encode('utf-8')]
        
        elif path == '/api/items':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            data = load_data(username)
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
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(item).encode('utf-8')]
        
        elif path == '/api/projects':
            username = get_session_username(environ)
            if not username:
                status = '401 Unauthorized'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
            
            data = load_data(username)
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
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(project).encode('utf-8')]
    
    # Handle PUT requests
    elif method == 'PUT':
        path_parts = path.split('/')
        if len(path_parts) < 4:
            status = '400 Bad Request'
            headers = [('Content-type', 'text/plain')]
            start_response(status, headers)
            return [b'Bad Request']
        
        username = get_session_username(environ)
        if not username:
            status = '401 Unauthorized'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
        
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        body = environ['wsgi.input'].read(content_length)
        updates = json.loads(body) if body else {}
        
        data = load_data(username)
        item_id = int(path_parts[3])
        
        if path_parts[2] == 'items':
            for i, item in enumerate(data['items']):
                if item['id'] == item_id:
                    data['items'][i].update(updates)
                    save_data(username, data)
                    status = '200 OK'
                    headers = [('Content-type', 'application/json')]
                    start_response(status, headers)
                    return [json.dumps(data['items'][i]).encode('utf-8')]
        elif path_parts[2] == 'projects':
            for i, project in enumerate(data['projects']):
                if project['id'] == item_id:
                    data['projects'][i].update(updates)
                    save_data(username, data)
                    status = '200 OK'
                    headers = [('Content-type', 'application/json')]
                    start_response(status, headers)
                    return [json.dumps(data['projects'][i]).encode('utf-8')]
        
        status = '404 Not Found'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [b'Not Found']
    
    # Handle DELETE requests
    elif method == 'DELETE':
        path_parts = path.split('/')
        if len(path_parts) < 4:
            status = '400 Bad Request'
            headers = [('Content-type', 'text/plain')]
            start_response(status, headers)
            return [b'Bad Request']
        
        username = get_session_username(environ)
        if not username:
            status = '401 Unauthorized'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps({"error": "Not authenticated"}).encode('utf-8')]
        
        data = load_data(username)
        item_id = int(path_parts[3])
        
        if path_parts[2] == 'items':
            data['items'] = [i for i in data['items'] if i['id'] != item_id]
            save_data(username, data)
            status = '204 No Content'
            headers = []
            start_response(status, headers)
            return [b'']
        elif path_parts[2] == 'projects':
            data['projects'] = [p for p in data['projects'] if p['id'] != item_id]
            # Remove project reference from items
            for item in data['items']:
                if item.get('projectId') == item_id:
                    item['projectId'] = None
                    item['status'] = 'inbox'
            save_data(username, data)
            status = '204 No Content'
            headers = []
            start_response(status, headers)
            return [b'']
        
        status = '404 Not Found'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [b'Not Found']
    
    # 404 for unknown routes
    status = '404 Not Found'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [b'Not Found']
