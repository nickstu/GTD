#!/usr/bin/env python3
"""
Migration script to convert plain text passwords to hashed passwords
Run this script to migrate your existing users.json file
"""
import json
import os
import hashlib
import secrets
import shutil

USERS_FILE = "users.json"
BACKUP_FILE = "users.json.backup"

def hash_password(password):
    """Hash a password using SHA256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + ':' + pwd_hash.hex()

def is_hashed(password_str):
    """Check if a password is already hashed (contains : separator)"""
    return ':' in password_str and len(password_str.split(':')) == 2

def migrate_users():
    """Migrate plain text passwords to hashed passwords"""
    
    if not os.path.exists(USERS_FILE):
        print(f"❌ {USERS_FILE} not found. Nothing to migrate.")
        return
    
    # Create backup
    shutil.copy2(USERS_FILE, BACKUP_FILE)
    print(f"✅ Created backup: {BACKUP_FILE}")
    
    # Load users
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    # Track changes
    migrated_count = 0
    already_hashed_count = 0
    
    # Migrate each user
    for username, user_data in users.items():
        password = user_data.get('password', '')
        
        if is_hashed(password):
            print(f"⏭️  {username}: Already hashed, skipping")
            already_hashed_count += 1
        else:
            hashed = hash_password(password)
            users[username]['password'] = hashed
            print(f"✅ {username}: Migrated (plain text: '{password}' -> hashed)")
            migrated_count += 1
    
    # Save updated users
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    
    print("\n" + "="*50)
    print(f"Migration complete!")
    print(f"  - Migrated: {migrated_count} users")
    print(f"  - Already hashed: {already_hashed_count} users")
    print(f"  - Backup saved to: {BACKUP_FILE}")
    print("="*50)
    
    if migrated_count > 0:
        print("\n⚠️  IMPORTANT: Keep the backup file in case you need to rollback!")
        print(f"   To rollback: mv {BACKUP_FILE} {USERS_FILE}")

if __name__ == "__main__":
    print("GTD Password Migration Script")
    print("="*50)
    print("This script will convert plain text passwords to hashed passwords.")
    print(f"File to migrate: {USERS_FILE}")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        migrate_users()
    else:
        print("Migration cancelled.")
