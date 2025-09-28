# Database Backup Restore Troubleshooting Guide

## Issue: "Failed to restore backup" Error

Based on the investigation, here are the detailed troubleshooting steps to resolve backup restore issues:

## Root Cause Analysis

The investigation revealed that the restore functionality is working correctly at the backend level. The issue appears to be related to:

1. **Authentication Requirements**: The restore API endpoint requires user authentication
2. **Session Management**: Browser sessions may expire or become invalid
3. **File Upload Process**: Issues with the file upload mechanism in the browser

## Troubleshooting Steps

### Step 1: Verify User Authentication

1. **Check if you're logged in**:

   - Ensure you're logged into the system
   - If you see a login page, log in with your credentials
   - Default credentials: username `admin`, password `admin123`

2. **Refresh your session**:
   - If you've been idle for a while, your session may have expired
   - Log out and log back in to refresh your session

### Step 2: Verify Backup File Integrity

1. **Check file format**:

   - Ensure the backup file has a `.db` extension
   - File should be a valid SQLite database
   - Typical file size: 45KB - 55KB for a restaurant database

2. **Test backup file validity**:
   ```bash
   # Run this command in the restaurant directory
   python test_backup.py
   ```

### Step 3: Browser-Specific Troubleshooting

1. **Clear browser cache**:

   - Press `Ctrl + Shift + Delete`
   - Clear cookies and cached data for the site

2. **Try a different browser**:

   - Test with Chrome, Firefox, or Edge
   - Disable browser extensions that might interfere

3. **Check browser console**:
   - Press `F12` to open developer tools
   - Look for JavaScript errors in the Console tab
   - Check Network tab for failed requests

### Step 4: File Upload Troubleshooting

1. **File size limitations**:

   - Ensure backup file is under 16MB (Flask default)
   - Check if file is corrupted or incomplete

2. **File permissions**:
   - Ensure the backup file is readable
   - Try copying the file to a different location

### Step 5: Server-Side Verification

1. **Check Flask server logs**:

   - Look at the terminal running the Flask server
   - Check for any error messages during restore attempts

2. **Verify server is running**:
   - Ensure Flask server is active on `http://127.0.0.1:5000`
   - Restart the server if necessary: `python app.py`

## Step-by-Step Restore Process

### Method 1: Web Interface (Recommended)

1. **Login to the system**:

   - Go to `http://127.0.0.1:5000`
   - Login with your credentials

2. **Navigate to Settings**:

   - Click on "Settings" in the navigation menu
   - Go to the "Backup & Restore" tab

3. **Select backup file**:

   - Click "Choose File" under "Database Restore"
   - Select your `.db` backup file

4. **Perform restore**:
   - Click "Restore Backup"
   - Confirm the action when prompted
   - Wait for the success message
   - Refresh the page to see restored data

### Method 2: Manual File Replacement (Advanced)

⚠️ **Warning**: Only use this method if the web interface fails

1. **Stop the Flask server**:

   - Press `Ctrl + C` in the terminal running the server

2. **Backup current database**:

   ```bash
   copy restaurant.db restaurant_backup_current.db
   ```

3. **Replace database file**:

   ```bash
   copy "path\to\your\backup.db" restaurant.db
   ```

4. **Restart the server**:
   ```bash
   python app.py
   ```

## Common Error Messages and Solutions

### "No backup file provided"

- **Cause**: File not selected or upload failed
- **Solution**: Ensure a file is selected before clicking restore

### "Invalid backup file - not a valid SQLite database"

- **Cause**: Corrupted or wrong file format
- **Solution**: Verify file integrity, try a different backup

### "Failed to restore backup" (Generic)

- **Cause**: Various issues including authentication, file access, or server errors
- **Solution**: Follow all troubleshooting steps above

### HTTP 302 Redirect to Login

- **Cause**: Session expired or not authenticated
- **Solution**: Log out and log back in

## Prevention Tips

1. **Regular Testing**:

   - Test backup and restore functionality regularly
   - Keep multiple backup copies

2. **Session Management**:

   - Don't leave the system idle for extended periods
   - Log out properly when finished

3. **File Management**:

   - Store backup files in a secure, accessible location
   - Use descriptive filenames with timestamps

4. **System Maintenance**:
   - Keep the Flask server running consistently
   - Monitor server logs for any issues

## Technical Details

- **Backup File Format**: SQLite database (.db)
- **Expected Tables**: users, menu_items, tables, waiters, orders, order_items, payments, settings
- **Authentication**: Session-based authentication required
- **File Upload**: Uses FormData with multipart/form-data encoding
- **Server Response**: JSON with success/error status

## Contact Support

If the issue persists after following all troubleshooting steps:

1. Note the exact error message
2. Check browser console for JavaScript errors
3. Review Flask server logs for backend errors
4. Document the steps that led to the error

The restore functionality has been thoroughly tested and verified to work correctly when proper authentication and file integrity requirements are met.
