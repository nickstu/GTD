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
    """Returns the complete HTML for the GTD app"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GTD Task Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
            background: #1a1a1a; 
            color: #e0e0e0; 
            line-height: 1.6; 
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { 
            background: #2d2d2d; 
            padding: 15px 0; 
            border-bottom: 2px solid #3d3d3d; 
            margin-bottom: 30px; 
        }
        header .container { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        h1 { color: #4a9eff; font-size: 1.8em; }
        .user-info { 
            display: flex; 
            align-items: center; 
            gap: 15px; 
        }
        button { 
            background: #4a9eff; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 14px; 
        }
        button:hover { background: #3a8eef; }
        button.secondary { background: #3d3d3d; }
        button.secondary:hover { background: #4d4d4d; }
        button.danger { background: #e74c3c; }
        button.danger:hover { background: #c0392b; }
        .login-screen { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 80vh; 
        }
        .login-box { 
            background: #2d2d2d; 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
            width: 100%; 
            max-width: 400px; 
        }
        .login-box h2 { 
            color: #4a9eff; 
            margin-bottom: 30px; 
            text-align: center; 
        }
        .form-group { margin-bottom: 20px; }
        label { 
            display: block; 
            margin-bottom: 5px; 
            color: #b0b0b0; 
        }
        input { 
            width: 100%; 
            padding: 10px; 
            background: #1a1a1a; 
            border: 1px solid #3d3d3d; 
            border-radius: 4px; 
            color: #e0e0e0; 
            font-size: 14px; 
        }
        input:focus { 
            outline: none; 
            border-color: #4a9eff; 
        }
        .error { 
            color: #e74c3c; 
            margin-top: 10px; 
            font-size: 14px; 
        }
        .dashboard { display: none; }
        .dashboard.active { display: block; }
        .sections { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
        }
        .section { 
            background: #2d2d2d; 
            padding: 20px; 
            border-radius: 8px; 
            min-height: 300px; 
        }
        .section h2 { 
            color: #4a9eff; 
            margin-bottom: 15px; 
            font-size: 1.3em; 
        }
        .add-item-form { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
        }
        .add-item-form input { flex: 1; }
        .item { 
            background: #3d3d3d; 
            padding: 12px; 
            margin-bottom: 10px; 
            border-radius: 4px; 
            cursor: move; 
            border-left: 3px solid #4a9eff; 
        }
        .item.dragging { opacity: 0.5; }
        .item.done { 
            opacity: 0.6; 
            text-decoration: line-through; 
            border-left-color: #666; 
        }
        .item-title { 
            font-weight: 500; 
            margin-bottom: 5px; 
            color: #e0e0e0; 
        }
        .item-meta { 
            font-size: 12px; 
            color: #888; 
            display: flex; 
            gap: 15px; 
            flex-wrap: wrap; 
        }
        .item-actions { 
            margin-top: 10px; 
            display: flex; 
            gap: 8px; 
        }
        .item-actions button { 
            padding: 5px 10px; 
            font-size: 12px; 
        }
        .project { 
            background: #3d3d3d; 
            padding: 15px; 
            margin-bottom: 15px; 
            border-radius: 4px; 
            border-left: 3px solid #9b59b6; 
        }
        .project-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 10px; 
        }
        .project-title { 
            font-weight: 600; 
            color: #e0e0e0; 
            font-size: 1.1em; 
        }
        .project-items { 
            margin-left: 10px; 
        }
        .drop-zone { 
            min-height: 50px; 
            border: 2px dashed #4d4d4d; 
            border-radius: 4px; 
            padding: 10px; 
            margin-top: 10px; 
        }
        .drop-zone.drag-over { 
            border-color: #4a9eff; 
            background: #2a2a2a; 
        }
        textarea { 
            width: 100%; 
            min-height: 100px; 
            padding: 10px; 
            background: #1a1a1a; 
            border: 1px solid #3d3d3d; 
            border-radius: 4px; 
            color: #e0e0e0; 
            font-family: inherit; 
            resize: vertical; 
        }
        textarea:focus { 
            outline: none; 
            border-color: #4a9eff; 
        }
        .modal { 
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.7); 
            z-index: 1000; 
        }
        .modal.active { display: flex; }
        .modal-content { 
            background: #2d2d2d; 
            padding: 30px; 
            border-radius: 8px; 
            max-width: 600px; 
            width: 90%; 
            margin: auto; 
            max-height: 80vh; 
            overflow-y: auto; 
        }
        .modal-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 20px; 
        }
        .modal-header h2 { color: #4a9eff; }
        .close-btn { 
            background: none; 
            color: #888; 
            font-size: 24px; 
            padding: 0; 
            width: 30px; 
            height: 30px; 
        }
        .close-btn:hover { color: #e0e0e0; }
        .admin-panel { 
            background: #2d2d2d; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .user-list { 
            margin-top: 20px; 
        }
        .user-item { 
            background: #3d3d3d; 
            padding: 12px; 
            margin-bottom: 10px; 
            border-radius: 4px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
    </style>
</head>
<body>
    <div id="loginScreen" class="login-screen">
        <div class="login-box">
            <h2>GTD Task Manager</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" required>
                </div>
                <button type="submit" style="width:100%;">Login</button>
                <div id="loginError" class="error"></div>
            </form>
        </div>
    </div>

    <div id="app" class="dashboard">
        <header>
            <div class="container">
                <h1>GTD Task Manager</h1>
                <div class="user-info">
                    <span id="currentUser"></span>
                    <button id="adminBtn" class="secondary" style="display:none;">Admin Panel</button>
                    <button id="logoutBtn" class="secondary">Logout</button>
                </div>
            </div>
        </header>

        <div class="container">
            <div class="sections">
                <div class="section">
                    <h2>📥 Inbox</h2>
                    <div class="add-item-form">
                        <input type="text" id="newItemInput" placeholder="Add new item...">
                        <button onclick="addItem()">Add</button>
                    </div>
                    <div id="inboxItems" class="drop-zone"></div>
                </div>

                <div class="section">
                    <h2>📅 Calendar (Items with Dates)</h2>
                    <div id="calendarItems"></div>
                </div>

                <div class="section">
                    <h2>⚡ Next Actions</h2>
                    <div id="nextActions"></div>
                </div>

                <div class="section">
                    <h2>💭 Someday/Maybe</h2>
                    <div id="somedayItems" class="drop-zone"></div>
                </div>
            </div>

            <div class="section" style="margin-top: 20px;">
                <h2>📁 Projects</h2>
                <div class="add-item-form">
                    <input type="text" id="newProjectInput" placeholder="New project name...">
                    <button onclick="addProject()">Add Project</button>
                </div>
                <div id="projectsList"></div>
            </div>
        </div>
    </div>

    <div id="itemModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Edit Item</h2>
                <button class="close-btn" onclick="closeItemModal()">&times;</button>
            </div>
            <div class="form-group">
                <label>Title</label>
                <input type="text" id="modalTitle">
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea id="modalNotes"></textarea>
            </div>
            <div class="form-group">
                <label>Due Date & Time</label>
                <input type="datetime-local" id="modalDueDate">
            </div>
            <button onclick="saveItemModal()">Save</button>
        </div>
    </div>

    <div id="adminModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Admin Panel</h2>
                <button class="close-btn" onclick="closeAdminModal()">&times;</button>
            </div>
            <div class="admin-panel">
                <h3 style="color: #4a9eff; margin-bottom: 15px;">Create New User</h3>
                <form id="createUserForm">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="newUsername" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="newPassword" required>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="newUserAdmin">
                            Admin privileges
                        </label>
                    </div>
                    <button type="submit">Create User</button>
                    <div id="createUserError" class="error"></div>
                </form>

                <div class="user-list">
                    <h3 style="color: #4a9eff; margin-bottom: 15px;">Existing Users</h3>
                    <div id="usersList"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentData = null;
        let currentItemId = null;
        let currentUsername = null;
        let isAdmin = false;

        // Authentication
        async function checkSession() {
            const res = await fetch('/api/check-session');
            const data = await res.json();
            if (data.authenticated) {
                currentUsername = data.username;
                isAdmin = data.isAdmin;
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('app').classList.add('active');
                document.getElementById('currentUser').textContent = `Logged in as: ${currentUsername}`;
                if (isAdmin) {
                    document.getElementById('adminBtn').style.display = 'block';
                }
                await loadData();
            }
        }

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            const data = await res.json();
            
            if (data.success) {
                await checkSession();
            } else {
                document.getElementById('loginError').textContent = data.message || 'Login failed';
            }
        });

        document.getElementById('logoutBtn').addEventListener('click', async () => {
            await fetch('/api/logout', {method: 'POST'});
            location.reload();
        });

        document.getElementById('adminBtn').addEventListener('click', () => {
            openAdminModal();
        });

        // Data management
        async function loadData() {
            const res = await fetch('/api/data');
            currentData = await res.json();
            render();
        }

        async function saveData() {
            await fetch('/api/data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(currentData)
            });
        }

        function getInboxItems() {
            return currentData.items.filter(item => 
                !item.projectId && 
                item.status !== 'someday' && 
                (item.status !== 'done' || item.previousStatus === 'active')
            );
        }

        function getSomedayItems() {
            return currentData.items.filter(item => 
                item.status === 'someday' || 
                (item.status === 'done' && item.previousStatus === 'someday')
            );
        }

        function getCalendarItems() {
            return currentData.items.filter(item => item.dueDatetime);
        }

        function getNextActions() {
            const actions = [];
            currentData.projects.forEach(project => {
                const projectItems = currentData.items
                    .filter(item => item.projectId === project.id && item.status !== 'done')
                    .sort((a, b) => a.position - b.position);
                if (projectItems.length > 0) {
                    actions.push({...projectItems[0], projectName: project.name});
                }
            });
            return actions;
        }

        function addItem() {
            const input = document.getElementById('newItemInput');
            const title = input.value.trim();
            if (!title) return;

            const newItem = {
                id: currentData.nextItemId++,
                title,
                notes: '',
                status: 'active',
                projectId: null,
                startTime: null,
                dueDatetime: null,
                position: getInboxItems().length,
                createdAt: new Date().toISOString()
            };
            currentData.items.push(newItem);
            input.value = '';
            saveData();
            render();
        }

        function addProject() {
            const input = document.getElementById('newProjectInput');
            const name = input.value.trim();
            if (!name) return;

            const newProject = {
                id: currentData.nextProjectId++,
                name,
                createdAt: new Date().toISOString()
            };
            currentData.projects.push(newProject);
            input.value = '';
            saveData();
            render();
        }

        function deleteItem(id) {
            if (!confirm('Delete this item?')) return;
            currentData.items = currentData.items.filter(item => item.id !== id);
            saveData();
            render();
        }

        function deleteProject(id) {
            if (!confirm('Delete this project and all its items?')) return;
            currentData.items = currentData.items.filter(item => item.projectId !== id);
            currentData.projects = currentData.projects.filter(project => project.id !== id);
            saveData();
            render();
        }

        function toggleDone(id) {
            const item = currentData.items.find(item => item.id === id);
            if (item.status === 'done') {
                item.status = item.previousStatus || 'active';
                delete item.previousStatus;
            } else {
                item.previousStatus = item.status;
                item.status = 'done';
            }
            saveData();
            render();
        }

        function moveToSomeday(id) {
            const item = currentData.items.find(item => item.id === id);
            item.status = 'someday';
            item.projectId = null;
            saveData();
            render();
        }

        function openItemModal(id) {
            currentItemId = id;
            const item = currentData.items.find(item => item.id === id);
            document.getElementById('modalTitle').value = item.title;
            document.getElementById('modalNotes').value = item.notes || '';
            document.getElementById('modalDueDate').value = item.dueDatetime || '';
            document.getElementById('itemModal').classList.add('active');
        }

        function closeItemModal() {
            document.getElementById('itemModal').classList.remove('active');
            currentItemId = null;
        }

        function saveItemModal() {
            const item = currentData.items.find(item => item.id === currentItemId);
            item.title = document.getElementById('modalTitle').value;
            item.notes = document.getElementById('modalNotes').value;
            item.dueDatetime = document.getElementById('modalDueDate').value || null;
            closeItemModal();
            saveData();
            render();
        }

        // Drag and drop
        function handleDragStart(e, itemId) {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', itemId);
            e.currentTarget.classList.add('dragging');
        }

        function handleDragEnd(e) {
            e.currentTarget.classList.remove('dragging');
        }

        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }

        function handleDrop(e, targetProjectId, targetStatus) {
            e.preventDefault();
            e.stopPropagation();
            
            const itemId = parseInt(e.dataTransfer.getData('text/plain'));
            const item = currentData.items.find(item => item.id === itemId);
            
            if (targetStatus === 'someday') {
                item.status = 'someday';
                item.projectId = null;
            } else if (targetProjectId) {
                item.projectId = targetProjectId;
                item.status = 'active';
                const projectItems = currentData.items
                    .filter(i => i.projectId === targetProjectId && i.id !== itemId)
                    .sort((a, b) => a.position - b.position);
                projectItems.forEach((i, idx) => i.position = idx);
                item.position = projectItems.length;
            } else {
                item.projectId = null;
                item.status = 'active';
                const inboxItems = getInboxItems().filter(i => i.id !== itemId);
                inboxItems.forEach((i, idx) => i.position = idx);
                item.position = inboxItems.length;
            }
            
            e.currentTarget.classList.remove('drag-over');
            saveData();
            render();
        }

        function handleItemDrop(e, targetItemId, targetProjectId) {
            e.preventDefault();
            e.stopPropagation();
            
            const draggedId = parseInt(e.dataTransfer.getData('text/plain'));
            if (draggedId === targetItemId) return;
            
            const draggedItem = currentData.items.find(item => item.id === draggedId);
            const targetItem = currentData.items.find(item => item.id === targetItemId);
            
            draggedItem.projectId = targetProjectId;
            draggedItem.status = targetItem.status;
            
            const projectItems = currentData.items
                .filter(item => item.projectId === targetProjectId && item.id !== draggedId)
                .sort((a, b) => a.position - b.position);
            
            const targetIndex = projectItems.findIndex(item => item.id === targetItemId);
            projectItems.splice(targetIndex, 0, draggedItem);
            projectItems.forEach((item, idx) => item.position = idx);
            
            saveData();
            render();
        }

        function renderItem(item, showProject = false) {
            const doneClass = item.status === 'done' ? 'done' : '';
            const projectName = showProject && item.projectId ? 
                currentData.projects.find(p => p.id === item.projectId)?.name : '';
            
            return `
                <div class="item ${doneClass}" draggable="true" 
                     ondragstart="handleDragStart(event, ${item.id})"
                     ondragend="handleDragEnd(event)"
                     ondragover="handleDragOver(event)"
                     ondrop="handleItemDrop(event, ${item.id}, ${item.projectId || null})">
                    <div class="item-title">${item.title}</div>
                    <div class="item-meta">
                        ${item.dueDatetime ? `📅 ${new Date(item.dueDatetime).toLocaleString()}` : ''}
                        ${projectName ? `📁 ${projectName}` : ''}
                    </div>
                    <div class="item-actions">
                        <button onclick="openItemModal(${item.id})">Edit</button>
                        <button onclick="toggleDone(${item.id})">${item.status === 'done' ? 'Undone' : 'Done'}</button>
                        ${!item.projectId && item.status !== 'someday' ? `<button onclick="moveToSomeday(${item.id})">→ Someday</button>` : ''}
                        <button class="danger" onclick="deleteItem(${item.id})">Delete</button>
                    </div>
                </div>
            `;
        }

        function render() {
            // Inbox
            const inboxItems = getInboxItems().sort((a, b) => a.position - b.position);
            document.getElementById('inboxItems').innerHTML = inboxItems.map(item => renderItem(item)).join('') || 
                '<div style="color: #888; padding: 20px; text-align: center;">No items in inbox</div>';

            // Someday
            const somedayItems = getSomedayItems();
            document.getElementById('somedayItems').innerHTML = somedayItems.map(item => renderItem(item)).join('') || 
                '<div style="color: #888; padding: 20px; text-align: center;">No someday items</div>';

            // Calendar
            const calendarItems = getCalendarItems().sort((a, b) => 
                new Date(a.dueDatetime) - new Date(b.dueDatetime));
            document.getElementById('calendarItems').innerHTML = calendarItems.map(item => renderItem(item, true)).join('') || 
                '<div style="color: #888; padding: 20px; text-align: center;">No items with dates</div>';

            // Next Actions
            const nextActions = getNextActions();
            document.getElementById('nextActions').innerHTML = nextActions.map(item => {
                const itemHtml = renderItem(item);
                return itemHtml.replace('<div class="item-title">', `<div class="item-title">📁 ${item.projectName}: `);
            }).join('') || '<div style="color: #888; padding: 20px; text-align: center;">No next actions</div>';

            // Projects
            const projectsHtml = currentData.projects.map(project => {
                const projectItems = currentData.items
                    .filter(item => item.projectId === project.id)
                    .sort((a, b) => a.position - b.position);
                
                return `
                    <div class="project">
                        <div class="project-header">
                            <div class="project-title">${project.name}</div>
                            <button class="danger" onclick="deleteProject(${project.id})">Delete</button>
                        </div>
                        <div class="project-items drop-zone" 
                             ondragover="handleDragOver(event)"
                             ondrop="handleDrop(event, ${project.id}, null)">
                            ${projectItems.map(item => renderItem(item)).join('') || 
                              '<div style="color: #888; padding: 10px;">Drop items here or drag from inbox</div>'}
                        </div>
                    </div>
                `;
            }).join('');
            document.getElementById('projectsList').innerHTML = projectsHtml || 
                '<div style="color: #888; padding: 20px; text-align: center;">No projects yet</div>';

            // Setup drop zones
            document.getElementById('inboxItems').ondragover = handleDragOver;
            document.getElementById('inboxItems').ondrop = (e) => handleDrop(e, null, 'inbox');
            document.getElementById('somedayItems').ondragover = handleDragOver;
            document.getElementById('somedayItems').ondrop = (e) => handleDrop(e, null, 'someday');
        }

        // Admin functions
        async function openAdminModal() {
            document.getElementById('adminModal').classList.add('active');
            await loadUsers();
        }

        function closeAdminModal() {
            document.getElementById('adminModal').classList.remove('active');
        }

        async function loadUsers() {
            const res = await fetch('/api/admin/users');
            const users = await res.json();
            
            const usersHtml = Object.entries(users).map(([username, data]) => `
                <div class="user-item">
                    <div>
                        <strong>${username}</strong>
                        ${data.isAdmin ? ' <span style="color: #4a9eff;">(Admin)</span>' : ''}
                    </div>
                    ${username !== 'admin' ? `<button class="danger" onclick="deleteUser('${username}')">Delete</button>` : ''}
                </div>
            `).join('');
            
            document.getElementById('usersList').innerHTML = usersHtml;
        }

        document.getElementById('createUserForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newPassword').value;
            const isAdmin = document.getElementById('newUserAdmin').checked;
            
            const res = await fetch('/api/admin/create-user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password, isAdmin})
            });
            const data = await res.json();
            
            if (data.success) {
                document.getElementById('createUserForm').reset();
                document.getElementById('createUserError').textContent = '';
                await loadUsers();
            } else {
                document.getElementById('createUserError').textContent = data.message;
            }
        });

        async function deleteUser(username) {
            if (!confirm(`Delete user "${username}"?`)) return;
            
            const res = await fetch('/api/admin/delete-user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username})
            });
            const data = await res.json();
            
            if (data.success) {
                await loadUsers();
            } else {
                alert(data.message);
            }
        }

        // Initialize
        checkSession();
    </script>
</body>
</html>'''

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
                    return [json.dumps({"success": True}).encode('utf-8')]
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
                response = {"success": True}
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(response).encode('utf-8')]
        
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
                
                response = {"success": True}
            
            status = '200 OK'
            headers = [('Content-type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(response).encode('utf-8')]
    
    # 404 for unknown routes
    status = '404 Not Found'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [b'Not Found']
