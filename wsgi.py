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
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GTD Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; 
            padding: 20px; 
            background: #1a1d23; 
            color: #e4e6eb;
        }
        .container { max-width: 1800px; margin: 0 auto; }
        header { margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }
        h1 { font-size: 24px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
        
        .user-info { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            font-size: 14px; 
            color: #adb5bd;
        }
        
        .logout-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }
        
        .logout-btn:hover {
            background: #bb2d3b;
        }
        
        #loginModal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }
        
        .login-box {
            background: #242831;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            width: 400px;
            max-width: 90%;
        }
        
        .login-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 24px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .login-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #3a3f4b;
            border-radius: 6px;
            background: #1a1d23;
            color: #e4e6eb;
            font-size: 14px;
        }
        
        .login-btn {
            padding: 12px;
            background: #0d6efd;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        
        .login-btn:hover {
            background: #0b5ed7;
        }
        
        .login-error {
            color: #dc3545;
            font-size: 13px;
            text-align: center;
        }
        
        .login-info {
            color: #adb5bd;
            font-size: 12px;
            text-align: center;
            margin-top: 12px;
        }
        
        .admin-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            margin-right: 8px;
        }
        
        .admin-btn:hover {
            background: #5c636a;
        }
        
        #adminPanel {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }
        
        #adminPanel.show {
            display: flex;
        }
        
        .admin-box {
            background: #242831;
            padding: 30px;
            border-radius: 12px;
            width: 600px;
            max-width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .admin-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
        }
        
        .admin-section {
            margin-bottom: 30px;
        }
        
        .admin-section h3 {
            font-size: 16px;
            margin-bottom: 12px;
            color: #adb5bd;
        }
        
        .user-list {
            background: #1a1d23;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 16px;
        }
        
        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            border-bottom: 1px solid #3a3f4b;
        }
        
        .user-item:last-child {
            border-bottom: none;
        }
        
        .user-badge {
            background: #0d6efd;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 8px;
        }
        
        .delete-user-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .delete-user-btn:hover {
            background: #bb2d3b;
        }
        
        .create-user-form {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .admin-close-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            width: 100%;
            margin-top: 16px;
        }
        
        .admin-close-btn:hover {
            background: #5c636a;
        }
        
        #appContent {
            display: none;
        }
        
        #appContent.show {
            display: block;
        }
        
        .grid-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .projects-row { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 10px; }
        
        .pane {
            background: #242831;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            height: 500px;
            overflow: hidden;
        }
        
        .pane-header {
            padding: 12px 16px;
            border-bottom: 1px solid #3a3f4b;
            background: #2a2f3a;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .pane-content {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }
        
        .item {
            background: #2a2f3a;
            border: 1px solid #3a3f4b;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 8px;
            cursor: move;
            transition: all 0.2s;
            position: relative;
        }
        
        .item:hover {
            border-color: #5a6170;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .item.dragging {
            opacity: 0.5;
        }
        
        .drop-target-hover {
            background: #3a4555 !important;
            border-color: #0d6efd !important;
            box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.3) !important;
        }
        
        .drop-target-project {
            background: #2a3545 !important;
            border: 2px dashed #0d6efd !important;
        }
        
        .insert-indicator {
            position: absolute;
            left: 0;
            right: 0;
            height: 3px;
            background: #0d6efd;
            border-radius: 2px;
            box-shadow: 0 0 8px rgba(13, 110, 253, 0.6);
            animation: pulse 0.6s ease-in-out infinite;
            pointer-events: none;
            z-index: 100;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scaleY(1); }
            50% { opacity: 0.7; transform: scaleY(1.5); }
        }
        
        .pane-content.drop-zone-active {
            background: rgba(13, 110, 253, 0.05);
            border: 2px dashed #0d6efd;
            border-radius: 8px;
        }
        
        .project-pane.drop-zone-active {
            background: rgba(13, 110, 253, 0.08) !important;
            border: 2px solid #0d6efd !important;
        }
        
        .item-title {
            font-weight: 500;
            font-size: 14px;
            margin-bottom: 4px;
        }
        
        .item.done .item-title {
            text-decoration: line-through;
            color: #6c757d;
            opacity: 0.6;
        }
        
        .item-meta {
            display: flex;
            gap: 8px;
            font-size: 11px;
            color: #6c757d;
            flex-wrap: wrap;
        }
        
        .item-date {
            color: #fd7e14;
        }
        
        .item-project {
            color: #0d6efd;
        }
        
        .quick-capture {
            padding: 12px;
            background: #2a2f3a;
            border-bottom: 1px solid #3a3f4b;
        }
        
        .quick-capture input {
            width: 100%;
            padding: 8px;
            border: 1px solid #3a3f4b;
            border-radius: 4px;
            margin-bottom: 6px;
            font-size: 13px;
            background: #1a1d23;
            color: #e4e6eb;
        }
        
        .quick-capture-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 6px;
        }
        
        .quick-capture button {
            width: 100%;
            padding: 8px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }
        
        .quick-capture button:hover {
            background: #218838;
        }
        
        .project-pane {
            min-width: 300px;
            flex-shrink: 0;
            background: #2a2f3a;
            border: 1px solid #3a3f4b;
            border-radius: 8px;
            padding: 12px;
            height: fit-content;
            position: relative;
        }
        
        .project-header {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: #6c757d;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
            cursor: pointer;
        }
        
        .project-header:hover {
            color: #0d6efd;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #adb5bd;
            font-size: 12px;
        }
        
        .btn-new-project {
            background: #0d6efd;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            margin: 8px;
        }
        
        .btn-new-project:hover {
            background: #0b5ed7;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .modal.show {
            display: flex;
        }
        
        .modal-content {
            background: #242831;
            padding: 24px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-header {
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 20px;
            font-weight: 600;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            font-size: 14px;
        }
        
        .form-control {
            width: 100%;
            padding: 10px;
            border: 1px solid #3a3f4b;
            border-radius: 6px;
            font-size: 14px;
            background: #1a1d23;
            color: #e4e6eb;
        }
        
        textarea.form-control {
            resize: vertical;
            min-height: 80px;
        }
        
        .form-actions {
            display: flex;
            gap: 8px;
            justify-content: flex-end;
            margin-top: 20px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        
        .btn-primary {
            background: #0d6efd;
            color: white;
        }
        
        .btn-primary:hover {
            background: #0b5ed7;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5c636a;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-danger:hover {
            background: #bb2d3b;
        }
        
        .checkbox-wrapper {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .checkbox {
            width: 18px;
            height: 18px;
            border: 2px solid #5a6170;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        
        .checkbox.done {
            background: #0d6efd;
            border-color: #0d6efd;
        }
        
        .checkbox.done::after {
            content: '✓';
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        
        .item-with-checkbox {
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }
        
        .item-details {
            flex: 1;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1d23;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #5a6170;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #6c757d;
        }
    </style>
</head>
<body>
    <!-- Login Modal -->
    <div id="loginModal">
        <div class="login-box">
            <h1 class="login-title">GTD Login</h1>
            <form class="login-form" onsubmit="login(event)">
                <input type="text" id="loginUsername" class="login-input" placeholder="Username" required autocomplete="username">
                <input type="password" id="loginPassword" class="login-input" placeholder="Password" required autocomplete="current-password">
                <button type="submit" class="login-btn">Login</button>
                <div id="loginError" class="login-error"></div>
                <div class="login-info">Default admin account: username "admin", password "admin"</div>
            </form>
        </div>
    </div>
    
    <div id="appContent" class="container">
        <header>
            <h1>GTD</h1>
            <div class="user-info">
                <button id="adminBtn" class="admin-btn" onclick="showAdminPanel()" style="display:none;">Admin Panel</button>
                <span>👤 <span id="currentUser"></span></span>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </header>
        
        <!-- Top Row: Inbox, Calendar, Next Actions, Someday -->
        <div class="grid-row">
            <div class="pane" data-status="inbox">
                <div class="pane-header">📥 Inbox</div>
                <div class="quick-capture">
                    <input type="text" id="quickTitle" placeholder="Quick capture...">
                    <div class="quick-capture-row">
                        <input type="date" id="quickDate">
                        <input type="time" id="quickTime">
                    </div>
                    <button onclick="quickCapture()">Add</button>
                </div>
                <div class="pane-content" id="inbox-content"></div>
            </div>
            
            <div class="pane">
                <div class="pane-header">📅 Calendar</div>
                <div class="pane-content" id="calendar-content"></div>
            </div>
            
            <div class="pane">
                <div class="pane-header">⚡ Next Actions</div>
                <div class="pane-content" id="next-content"></div>
            </div>
            
            <div class="pane" data-status="someday">
                <div class="pane-header">📦 Someday</div>
                <div class="pane-content" id="someday-content"></div>
            </div>
        </div>
        
        <!-- Bottom Row: Projects -->
        <div class="pane" style="height: 400px;">
            <div class="pane-header">
                🗂️ Projects
                <button class="btn-new-project" onclick="newProject()">+ New Project</button>
            </div>
            <div class="projects-row" id="projects-content"></div>
        </div>
    </div>
    
    <!-- Admin Panel -->
    <div id="adminPanel" onclick="if(event.target === this) closeAdminPanel()">
        <div class="admin-box">
            <h2 class="admin-title">Admin Panel</h2>
            
            <div class="admin-section">
                <h3>Users</h3>
                <div id="userList" class="user-list"></div>
            </div>
            
            <div class="admin-section">
                <h3>Create New User</h3>
                <form class="create-user-form" onsubmit="createUser(event)">
                    <input type="text" id="newUsername" class="form-control" placeholder="Username" required>
                    <input type="password" id="newPassword" class="form-control" placeholder="Password" required>
                    <button type="submit" class="btn btn-primary">Create User</button>
                    <div id="createUserError" class="login-error"></div>
                </form>
            </div>
            
            <button class="admin-close-btn" onclick="closeAdminPanel()">Close</button>
        </div>
    </div>

    <!-- Item Edit Modal -->
    <div id="itemModal" class="modal" onclick="if(event.target === this) closeItemModal()">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">Edit Item</h2>
            </div>
            <div class="form-group">
                <label class="form-label">Title</label>
                <input type="text" id="editTitle" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea id="editNotes" class="form-control"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Due Date</label>
                <input type="date" id="editDate" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">Start Time</label>
                <input type="time" id="editTime" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">Project</label>
                <select id="editProject" class="form-control">
                    <option value="">None</option>
                </select>
            </div>
            <div class="form-actions">
                <button class="btn btn-danger" onclick="deleteItem()">Delete</button>
                <button class="btn btn-secondary" onclick="closeItemModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveItem()">Save</button>
            </div>
        </div>
    </div>
    
    <!-- Project Edit Modal -->
    <div id="projectModal" class="modal" onclick="if(event.target === this) closeProjectModal()">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="projectModalTitle">New Project</h2>
            </div>
            <div class="form-group">
                <label class="form-label">Name</label>
                <input type="text" id="projectName" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">Desired Outcome</label>
                <textarea id="projectOutcome" class="form-control"></textarea>
            </div>
            <div class="form-actions">
                <button class="btn btn-danger" id="deleteProjectBtn" onclick="deleteProject()" style="display:none;">Delete</button>
                <button class="btn btn-secondary" onclick="closeProjectModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveProject()">Save</button>
            </div>
        </div>
    </div>

    <script>
        let data = { projects: [], items: [], nextProjectId: 1, nextItemId: 1 };
        let currentItem = null;
        let currentProject = null;
        let draggedItem = null;
        let currentUser = null;
        let isAdmin = false;
        
        // Check session on load
        async function checkSession() {
            try {
                const response = await fetch('/api/check-session');
                const result = await response.json();
                if (result.authenticated) {
                    currentUser = result.username;
                    isAdmin = result.isAdmin || false;
                    document.getElementById('currentUser').textContent = currentUser;
                    if (isAdmin) {
                        document.getElementById('adminBtn').style.display = 'inline-block';
                    }
                    document.getElementById('loginModal').style.display = 'none';
                    document.getElementById('appContent').classList.add('show');
                    await loadData();
                }
            } catch (error) {
                console.error('Session check failed:', error);
            }
        }
        
        async function login(e) {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentUser = result.username;
                    isAdmin = result.isAdmin || false;
                    document.getElementById('currentUser').textContent = currentUser;
                    if (isAdmin) {
                        document.getElementById('adminBtn').style.display = 'inline-block';
                    }
                    document.getElementById('loginModal').style.display = 'none';
                    document.getElementById('appContent').classList.add('show');
                    document.getElementById('loginError').textContent = '';
                    await loadData();
                } else {
                    document.getElementById('loginError').textContent = result.message;
                }
            } catch (error) {
                document.getElementById('loginError').textContent = 'Login failed. Please try again.';
            }
        }
        
        async function logout() {
            if (!confirm('Logout?')) return;
            
            try {
                await fetch('/api/logout', { method: 'POST' });
                location.reload();
            } catch (error) {
                console.error('Logout failed:', error);
            }
        }
        
        async function showAdminPanel() {
            if (!isAdmin) return;
            
            document.getElementById('adminPanel').classList.add('show');
            await loadUsers();
        }
        
        function closeAdminPanel() {
            document.getElementById('adminPanel').classList.remove('show');
        }
        
        async function loadUsers() {
            try {
                const response = await fetch('/api/admin/list-users', { method: 'POST' });
                const result = await response.json();
                
                const userListHtml = result.users.map(user => `
                    <div class="user-item">
                        <div>
                            <strong>${user.username}</strong>
                            ${user.isAdmin ? '<span class="user-badge">ADMIN</span>' : ''}
                        </div>
                        ${user.username !== 'admin' ? 
                            `<button class="delete-user-btn" onclick="deleteUser('${user.username}')">Delete</button>` : 
                            ''}
                    </div>
                `).join('');
                
                document.getElementById('userList').innerHTML = userListHtml;
            } catch (error) {
                console.error('Failed to load users:', error);
            }
        }
        
        async function createUser(e) {
            e.preventDefault();
            
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newPassword').value;
            
            try {
                const response = await fetch('/api/admin/create-user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('newUsername').value = '';
                    document.getElementById('newPassword').value = '';
                    document.getElementById('createUserError').textContent = '';
                    await loadUsers();
                    alert(result.message);
                } else {
                    document.getElementById('createUserError').textContent = result.message;
                }
            } catch (error) {
                document.getElementById('createUserError').textContent = 'Failed to create user';
            }
        }
        
        async function deleteUser(username) {
            if (!confirm(`Delete user "${username}"? This will also delete their data.`)) return;
            
            try {
                const response = await fetch('/api/admin/delete-user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    await loadUsers();
                    alert(result.message);
                } else {
                    alert(result.message);
                }
            } catch (error) {
                alert('Failed to delete user');
            }
        }
        
        async function loadData() {
            const response = await fetch('/api/data');
            data = await response.json();
            render();
        }
        
        function getInboxItems() {
            return data.items.filter(i => 
                i.status === 'inbox' || 
                (i.status === 'done' && !i.projectId && (!i.previousStatus || i.previousStatus === 'inbox'))
            );
        }
        
        function getSomedayItems() {
            return data.items.filter(i => 
                i.status === 'someday' || 
                (i.status === 'done' && !i.projectId && i.previousStatus === 'someday')
            );
        }
        
        function getCalendarItems() {
            return data.items
                .filter(i => i.dueDatetime)
                .sort((a, b) => {
                    const dateA = new Date(a.dueDatetime).getTime();
                    const dateB = new Date(b.dueDatetime).getTime();
                    if (dateA !== dateB) return dateA - dateB;
                    return (a.startTime || '').localeCompare(b.startTime || '');
                });
        }
        
        function getNextActions() {
            const nextActions = [];
            data.projects.forEach(project => {
                const projectItems = data.items
                    .filter(i => i.projectId === project.id && i.status === 'projects')
                    .sort((a, b) => (a.position || 0) - (b.position || 0));
                // Get first non-done item
                const firstUndone = projectItems.find(i => i.status !== 'done');
                if (firstUndone) {
                    nextActions.push({ ...firstUndone, project });
                }
            });
            return nextActions;
        }
        
        function formatDate(dateStr) {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
        
        function renderItem(item, showCheckbox = true) {
            const isDone = item.status === 'done';
            
            let html = '<div class="item' + (isDone ? ' done' : '') + '" draggable="true" data-id="' + item.id + '">';
            
            if (showCheckbox) {
                html += '<div class="item-with-checkbox">';
                html += '<div class="checkbox ' + (isDone ? 'done' : '') + '" onclick="toggleDone(' + item.id + ', event)"></div>';
                html += '<div class="item-details">';
            }
            
            html += '<div class="item-title">' + item.title + '</div>';
            
            if (item.dueDatetime || item.startTime) {
                html += '<div class="item-meta">';
                if (item.dueDatetime) {
                    html += '<span class="item-date">📅 ' + formatDate(item.dueDatetime);
                    if (item.startTime) html += ' ' + item.startTime;
                    html += '</span>';
                }
                html += '</div>';
            }
            
            if (showCheckbox) {
                html += '</div></div>';
            }
            
            html += '</div>';
            return html;
        }
        
        function render() {
            // Inbox
            document.getElementById('inbox-content').innerHTML = 
                getInboxItems().map(i => renderItem(i)).join('');
            
            // Calendar
            const calItems = getCalendarItems();
            document.getElementById('calendar-content').innerHTML = 
                calItems.length ? calItems.map(i => renderItem(i, false)).join('') : '<div class="empty-state">No scheduled items</div>';
            
            // Next Actions
            const nextActions = getNextActions();
            document.getElementById('next-content').innerHTML = 
                nextActions.length ? nextActions.map(i => renderItem(i, false)).join('') : '<div class="empty-state">No next actions</div>';
            
            // Someday
            document.getElementById('someday-content').innerHTML = 
                getSomedayItems().map(i => renderItem(i)).join('');
            
            // Projects
            let projectsHtml = '';
            data.projects.forEach(project => {
                const projectItems = data.items
                    .filter(i => i.projectId === project.id && (i.status === 'projects' || i.status === 'done'))
                    .sort((a, b) => (a.position || 0) - (b.position || 0));
                
                projectsHtml += '<div class="project-pane" data-project-id="' + project.id + '">';
                projectsHtml += '<div class="project-header" onclick="editProject(' + project.id + ')">' + project.name + '</div>';
                projectsHtml += projectItems.map(i => renderItem(i)).join('');
                if (projectItems.length === 0) {
                    projectsHtml += '<div class="empty-state" style="padding: 20px; font-size: 10px;">Empty Project</div>';
                }
                projectsHtml += '</div>';
            });
            
            if (data.projects.length === 0) {
                projectsHtml = '<div class="empty-state">No projects. Click "+ New Project" to create one.</div>';
            }
            
            document.getElementById('projects-content').innerHTML = projectsHtml;
            
            // Update project selector in edit modal
            const projectSelect = document.getElementById('editProject');
            projectSelect.innerHTML = '<option value="">None</option>' + 
                data.projects.map(p => '<option value="' + p.id + '">' + p.name + '</option>').join('');
            
            // Attach drag listeners
            document.querySelectorAll('.item').forEach(el => {
                el.addEventListener('dragstart', handleDragStart);
                el.addEventListener('dragend', handleDragEnd);
                el.addEventListener('dragover', handleDragOver);
                el.addEventListener('dragenter', handleDragEnter);
                el.addEventListener('dragleave', handleDragLeave);
                el.addEventListener('drop', handleDrop);
                el.addEventListener('click', function(e) {
                    if (!e.target.classList.contains('checkbox')) {
                        openItemModal(parseInt(el.dataset.id));
                    }
                });
            });
            
            // Attach drop listeners
            document.querySelectorAll('[data-status]').forEach(el => {
                el.addEventListener('dragover', handleDragOver);
                el.addEventListener('dragenter', handleDragEnter);
                el.addEventListener('dragleave', handleDragLeave);
                el.addEventListener('drop', handleDrop);
            });
            
            document.querySelectorAll('[data-project-id]').forEach(el => {
                el.addEventListener('dragover', handleDragOver);
                el.addEventListener('dragenter', handleDragEnter);
                el.addEventListener('dragleave', handleDragLeave);
                el.addEventListener('drop', handleDrop);
            });
        }
        
        function handleDragStart(e) {
            draggedItem = parseInt(e.target.dataset.id);
            e.target.classList.add('dragging');
        }
        
        function handleDragEnd(e) {
            e.target.classList.remove('dragging');
            // Clean up all visual feedback
            document.querySelectorAll('.drop-target-hover, .drop-target-project, .drop-zone-active').forEach(el => {
                el.classList.remove('drop-target-hover', 'drop-target-project', 'drop-zone-active');
                el._dragDepth = 0; // Reset drag depth counters
            });
            document.querySelectorAll('.insert-indicator').forEach(el => el.remove());
            draggedItem = null;
        }
        
        function handleDragEnter(e) {
            if (!draggedItem) return;
            e.preventDefault();
            
            const target = e.currentTarget;
            const item = data.items.find(i => i.id === draggedItem);
            if (!item) return;
            
            // Track drag depth to prevent flickering from child elements
            if (!target._dragDepth) target._dragDepth = 0;
            target._dragDepth++;
            
            // Only apply visual feedback on first enter
            if (target._dragDepth !== 1) return;
            
            // Highlight drop zones
            if (target.classList.contains('item')) {
                const targetItemId = parseInt(target.dataset.id);
                const targetItem = data.items.find(i => i.id === targetItemId);
                
                // Check if this would be a reorder operation
                if (targetItem && targetItem.projectId && item.projectId === targetItem.projectId && item.status === 'projects') {
                    // Show insertion indicator for reordering - place it at top of target item
                    const existingIndicator = target.querySelector('.insert-indicator');
                    if (!existingIndicator) {
                        const indicator = document.createElement('div');
                        indicator.className = 'insert-indicator';
                        indicator.style.top = '-4px';
                        target.appendChild(indicator);
                    }
                } else if (targetItem && targetItem.projectId) {
                    // Show it will be added to this project
                    target.classList.add('drop-target-hover');
                }
            } else if (target.dataset.status || target.dataset.projectId) {
                // Highlight panes
                if (target.classList.contains('pane-content')) {
                    target.classList.add('drop-zone-active');
                } else if (target.classList.contains('project-pane')) {
                    target.classList.add('drop-zone-active');
                }
            }
        }
        
        function handleDragLeave(e) {
            if (!draggedItem) return;
            const target = e.currentTarget;
            
            // Track drag depth to prevent flickering from child elements
            if (!target._dragDepth) target._dragDepth = 0;
            target._dragDepth--;
            
            // Only remove visual feedback when fully leaving the element
            if (target._dragDepth > 0) return;
            
            // Remove highlights
            target.classList.remove('drop-target-hover', 'drop-target-project', 'drop-zone-active');
            
            // Remove insertion indicators from this element
            const indicators = target.querySelectorAll('.insert-indicator');
            indicators.forEach(ind => ind.remove());
        }
        
        function handleDragOver(e) {
            e.preventDefault();
        }
        
        async function handleDrop(e) {
            e.preventDefault();
            e.stopPropagation();  // Prevent bubbling to project pane
            
            // Clean up visual feedback
            document.querySelectorAll('.drop-target-hover, .drop-target-project, .drop-zone-active').forEach(el => {
                el.classList.remove('drop-target-hover', 'drop-target-project', 'drop-zone-active');
            });
            document.querySelectorAll('.insert-indicator').forEach(el => el.remove());
            
            if (!draggedItem) return;
            
            const item = data.items.find(i => i.id === draggedItem);
            if (!item) return;
            
            const target = e.currentTarget;
            
            // Check if dropped on another item
            if (target.classList.contains('item')) {
                const targetItemId = parseInt(target.dataset.id);
                const targetItem = data.items.find(i => i.id === targetItemId);
                
                // Only reorder if BOTH items are already in the same project (dragging within same project)
                if (targetItem && targetItem.projectId && item.projectId === targetItem.projectId && item.status === 'projects') {
                    const projectId = targetItem.projectId;
                    const projectItems = data.items
                        .filter(i => i.projectId === projectId && i.status === 'projects')
                        .sort((a, b) => (a.position || 0) - (b.position || 0));
                    
                    const oldIndex = projectItems.findIndex(i => i.id === draggedItem);
                    const newIndex = projectItems.findIndex(i => i.id === targetItemId);
                    
                    if (oldIndex !== -1 && newIndex !== -1 && oldIndex !== newIndex) {
                        // Build new order: remove dragged item, then insert at target position
                        const reordered = projectItems.filter(i => i.id !== draggedItem);
                        const draggedItemObj = projectItems[oldIndex];
                        reordered.splice(newIndex, 0, draggedItemObj);
                        
                        // Update all positions sequentially
                        for (let i = 0; i < reordered.length; i++) {
                            await fetch('/api/items/' + reordered[i].id, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ position: i })
                            });
                        }
                    }
                    await loadData();
                    return;
                }
                
                // If dropped on item but NOT reordering, treat it as dropping into that item's project
                if (targetItem && targetItem.projectId) {
                    const projectId = targetItem.projectId;
                    const projectItems = data.items.filter(i => i.projectId === projectId && i.status === 'projects');
                    const maxPos = projectItems.length > 0 ? Math.max(...projectItems.map(i => i.position || 0)) : -1;
                    
                    await fetch('/api/items/' + draggedItem, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: 'projects', projectId, position: maxPos + 1 })
                    });
                    await loadData();
                    return;
                }
            }
            
            const newStatus = target.dataset.status;
            const newProjectId = target.dataset.projectId;
            
            if (newStatus) {
                // Dropped into inbox or someday
                await fetch('/api/items/' + draggedItem, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus, projectId: null, position: 0 })
                });
            } else if (newProjectId) {
                // Dropped into a project pane
                const projectId = parseInt(newProjectId);
                const projectItems = data.items.filter(i => i.projectId === projectId && i.status === 'projects');
                const maxPos = projectItems.length > 0 ? Math.max(...projectItems.map(i => i.position || 0)) : -1;
                
                await fetch('/api/items/' + draggedItem, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'projects', projectId, position: maxPos + 1 })
                });
            }
            
            await loadData();
        }
        
        async function quickCapture() {
            const title = document.getElementById('quickTitle').value.trim();
            if (!title) return;
            
            const date = document.getElementById('quickDate').value;
            const time = document.getElementById('quickTime').value;
            
            await fetch('/api/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    status: 'inbox',
                    dueDatetime: date || null,
                    startTime: time || null,
                    position: 0
                })
            });
            
            document.getElementById('quickTitle').value = '';
            document.getElementById('quickDate').value = '';
            document.getElementById('quickTime').value = '';
            
            await loadData();
        }
        
        async function toggleDone(itemId, e) {
            e.stopPropagation();
            const item = data.items.find(i => i.id === itemId);
            if (!item) return;
            
            let updates = {};
            if (item.status === 'done') {
                // Restore to previous status (stored in notes field temporarily or use a better approach)
                // Check if it has a project -> projects, otherwise check previousStatus
                if (item.projectId) {
                    updates.status = 'projects';
                } else if (item.previousStatus) {
                    updates.status = item.previousStatus;
                    updates.previousStatus = null;
                } else {
                    updates.status = 'inbox';
                }
            } else {
                // Mark as done and store previous status
                updates.status = 'done';
                updates.previousStatus = item.status;
            }
            
            await fetch('/api/items/' + itemId, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            
            await loadData();
        }
        
        function openItemModal(itemId) {
            currentItem = data.items.find(i => i.id === itemId);
            if (!currentItem) return;
            
            document.getElementById('editTitle').value = currentItem.title;
            document.getElementById('editNotes').value = currentItem.notes || '';
            document.getElementById('editDate').value = currentItem.dueDatetime ? currentItem.dueDatetime.split('T')[0] : '';
            document.getElementById('editTime').value = currentItem.startTime || '';
            document.getElementById('editProject').value = currentItem.projectId || '';
            
            document.getElementById('itemModal').classList.add('show');
        }
        
        function closeItemModal() {
            document.getElementById('itemModal').classList.remove('show');
            currentItem = null;
        }
        
        async function saveItem() {
            if (!currentItem) return;
            
            const title = document.getElementById('editTitle').value.trim();
            if (!title) return;
            
            const updates = {
                title,
                notes: document.getElementById('editNotes').value || null,
                dueDatetime: document.getElementById('editDate').value || null,
                startTime: document.getElementById('editTime').value || null,
                projectId: parseInt(document.getElementById('editProject').value) || null
            };
            
            if (updates.projectId) {
                updates.status = 'projects';
            } else if (currentItem.status === 'projects') {
                updates.status = 'inbox';
            }
            
            await fetch('/api/items/' + currentItem.id, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            
            closeItemModal();
            await loadData();
        }
        
        async function deleteItem() {
            if (!currentItem || !confirm('Delete this item?')) return;
            
            await fetch('/api/items/' + currentItem.id, {
                method: 'DELETE'
            });
            
            closeItemModal();
            await loadData();
        }
        
        function newProject() {
            currentProject = null;
            document.getElementById('projectModalTitle').textContent = 'New Project';
            document.getElementById('projectName').value = '';
            document.getElementById('projectOutcome').value = '';
            document.getElementById('deleteProjectBtn').style.display = 'none';
            document.getElementById('projectModal').classList.add('show');
        }
        
        function editProject(projectId) {
            currentProject = data.projects.find(p => p.id === projectId);
            if (!currentProject) return;
            
            document.getElementById('projectModalTitle').textContent = 'Edit Project';
            document.getElementById('projectName').value = currentProject.name;
            document.getElementById('projectOutcome').value = currentProject.outcome || '';
            document.getElementById('deleteProjectBtn').style.display = 'inline-block';
            document.getElementById('projectModal').classList.add('show');
        }
        
        function closeProjectModal() {
            document.getElementById('projectModal').classList.remove('show');
            currentProject = null;
        }
        
        async function saveProject() {
            const name = document.getElementById('projectName').value.trim();
            if (!name) return;
            
            const projectData = {
                name,
                outcome: document.getElementById('projectOutcome').value || null,
                status: 'active'
            };
            
            if (currentProject) {
                await fetch('/api/projects/' + currentProject.id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(projectData)
                });
            } else {
                await fetch('/api/projects', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(projectData)
                });
            }
            
            closeProjectModal();
            await loadData();
        }
        
        async function deleteProject() {
            if (!currentProject || !confirm('Delete this project? Items will be moved to inbox.')) return;
            
            await fetch('/api/projects/' + currentProject.id, {
                method: 'DELETE'
            });
            
            closeProjectModal();
            await loadData();
        }
        
        // Keyboard shortcut for quick capture
        document.addEventListener('keydown', function(e) {
            if ((e.key === 'q' || e.key === 'c') && !e.ctrlKey && !e.metaKey && 
                document.activeElement.tagName !== 'INPUT' && 
                document.activeElement.tagName !== 'TEXTAREA') {
                document.getElementById('quickTitle').focus();
            }
        });
        
        // Enter key in quick capture
        document.getElementById('quickTitle').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') quickCapture();
        });
        
        // Initialize
        checkSession();
    </script>
</body>
</html>"""



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
