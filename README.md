# GTD Task Manager

A simple Getting Things Done (GTD) task management web app built with Python. Features multi-user authentication, drag-and-drop organization, and automatic calendar/next actions views.

## Features

- **Inbox**: Capture new items quickly
- **Calendar**: Automatic view of items with due dates
- **Next Actions**: First uncompleted item from each project
- **Someday/Maybe**: Park ideas for later
- **Projects**: Organize items into projects with drag-and-drop
- **Multi-user**: Admin-controlled user accounts with session authentication
- **Dark Theme**: Easy on the eyes

## Quick Start (Local)

```bash
python app.py
```

Opens automatically at http://localhost:8000

**Default login**: username `admin`, password `admin`

## PythonAnywhere Deployment

### Step 1: Upload Files

1. Log into your PythonAnywhere account
2. Go to **Files** tab
3. Create a new directory (e.g., `GTD`)
4. Upload these files:
   - `wsgi.py`
   - `.gitignore`

Or clone from GitHub:
```bash
git clone https://github.com/nickstu/GTD.git
cd GTD
```

### Step 2: Create Web App

1. Go to **Web** tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select **Python 3.10** (or latest available)

### Step 3: Configure WSGI

1. In the **Web** tab, find the "Code" section
2. Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. **Delete all the existing content**
4. Add this code:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/GTD'  # ← Change 'yourusername' to your PythonAnywhere username
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the working directory so data files are created in the right place
os.chdir(project_home)

# Import the WSGI application
from wsgi import application
```

**Important**: Replace `yourusername` with your actual PythonAnywhere username in the path above.

### Step 4: Set Working Directory

1. Still in the **Web** tab, find "Code" section
2. Set "Working directory" to: `/home/yourusername/GTD`
3. Set "Source code" to: `/home/yourusername/GTD`

### Step 5: Reload

1. Scroll to top of **Web** tab
2. Click the big green **"Reload"** button
3. Your app is now live at `yourusername.pythonanywhere.com`

## Data Storage

- `users.json` - User accounts (admin can create new users)
- `data_username.json` - Per-user GTD data (projects, items)

All stored as JSON files in the working directory.

## Admin Panel

Login as admin to:
- Create new user accounts
- Grant admin privileges to other users
- Delete users (and their data)

## Security Note

This app uses plain text passwords and is designed for personal/small team use. For production deployments with sensitive data, implement proper password hashing and HTTPS.

## License

MIT
