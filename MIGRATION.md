# Password Migration Guide

## Overview
Passwords are now stored as hashed values using PBKDF2-HMAC-SHA256 instead of plain text for better security.

## Migration Process

### For Deployed/Production Systems

1. **Stop the application** (if running)
   ```bash
   # Stop your GTD app server
   ```

2. **Backup your current users.json** (optional - script does this automatically)
   ```bash
   cp users.json users.json.manual-backup
   ```

3. **Run the migration script**
   ```bash
   python3 migrate_passwords.py
   ```
   
   The script will:
   - Create an automatic backup (`users.json.backup`)
   - Show which users are being migrated
   - Display the plain text passwords as they are converted (for your records)
   - Convert all plain text passwords to hashed format

4. **Verify the migration**
   - The script will show how many users were migrated
   - Check the output to confirm all expected users were processed

5. **Start the application** with the updated code
   ```bash
   python3 app.py
   ```

6. **Test login** with your existing passwords (they should still work!)

### Rollback (if needed)
If something goes wrong, you can restore the backup:
```bash
mv users.json.backup users.json
```

## Technical Details

- **Hashing Algorithm**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000
- **Salt**: 32-character random hex string (unique per password)
- **Format**: `salt:hash` (stored as single string)

## What Changed in the Code

1. **app.py**: 
   - Added `hash_password()` function to hash new passwords
   - Added `verify_password()` function to check passwords during login
   - Updated user creation to hash passwords
   - Updated admin default password to be hashed

2. **migrate_passwords.py**:
   - Standalone script to convert existing plain text passwords
   - Creates automatic backup
   - Detects already-hashed passwords (won't double-hash)

## Security Notes

- Old sessions remain valid during migration
- Users don't need to change their passwords
- The migration script shows plain text passwords before hashing (for admin reference)
- Keep the backup file secure as it contains plain text passwords
