# Restaurant Cashier Management System

A lightweight, fast, and beautiful restaurant management system designed to run locally on older hardware. Built with Python Flask backend, SQLite database, and responsive Bootstrap frontend.

## Features

### 🏪 Core Functionality

- **Session-based Authentication** - Secure cashier login system
- **Menu Management** - Add, edit, delete food and drink items
- **Table & Waiter Management** - Organize orders by table and staff
- **Order Processing** - Create, modify, and finalize orders
- **Payment Processing** - Support for cash, card, and digital payments
- **Receipt Printing** - Thermal printer support with beautiful formatting

### 📊 Reporting & Analytics

- **Dashboard** - Real-time sales overview with charts
- **Sales Reports** - Daily, weekly, monthly revenue tracking
- **Performance Analytics** - Top items, waiter performance, table analytics
- **Export Options** - CSV and PDF export capabilities

### 🎨 User Interface

- **Modern Design** - Clean Bootstrap-based interface
- **Dark Mode** - Toggle between light and dark themes
- **Mobile Friendly** - Responsive design for tablets and touch screens
- **POS-Style Buttons** - Large, easy-to-use interface elements
- **Keyboard Shortcuts** - Fast navigation for experienced users

### ⚡ Performance & Deployment

- **Lightweight** - Optimized for dual-core PCs with low RAM
- **Local Operation** - No internet required, all data stored locally
- **Auto-Start** - Windows service for automatic startup
- **Fast Loading** - Vanilla JavaScript for optimal performance

## System Requirements

- **Operating System**: Windows 7/8/10/11
- **Hardware**: Dual-core processor, 2GB RAM minimum
- **Software**: Python 3.7 or higher
- **Optional**: Thermal receipt printer (58mm or 80mm)

## Quick Start

### 1. Download and Setup

```bash
# Clone or download the project to your desired location
# Example: w:\Projects\restaurant\
```

### 2. Install Dependencies

```bash
# Navigate to the project directory
cd w:\Projects\restaurant

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Option A: Manual start
python app.py

# Option B: Use the batch script
start_restaurant.bat
```

### 4. Access the System

- Open your browser and go to: `http://localhost:5000`
- **Default Login**:
  - Username: `admin`
  - Password: `admin123`

## Auto-Start with Windows

### Method 1: Startup Folder (Simple)

1. Press `Win + R`, type `shell:startup`, press Enter
2. Copy `start_restaurant.bat` to the startup folder
3. The system will start automatically when Windows boots

### Method 2: Windows Service (Advanced)

1. Right-click `install_service.bat` and select "Run as administrator"
2. Follow the prompts to install the service
3. The system will run as a Windows service

## Configuration

### Restaurant Information

1. Login to the system
2. Go to **Settings** → **Restaurant Info**
3. Update your restaurant details:
   - Name, address, phone number
   - Tax rate and currency
   - Receipt formatting preferences

### Printer Setup

1. Go to **Settings** → **System**
2. Select your printer type:
   - Thermal 58mm
   - Thermal 80mm
   - Regular printer
3. Test printing from any order

### User Management

1. Go to **Settings** → **Users**
2. Add additional cashier accounts
3. Manage user permissions

## Usage Guide

### Creating Orders

1. Click **New Order** from the dashboard
2. Select table number and waiter
3. Add items from the menu
4. Adjust quantities as needed
5. Process payment (cash/card/digital)
6. Print receipt

### Menu Management

1. Go to **Menu** from the sidebar
2. Add new items with name, category, and price
3. Edit existing items by clicking the edit button
4. Use search and filters to find items quickly

### Viewing Reports

1. Go to **Reports** from the sidebar
2. Select date range (daily/weekly/monthly)
3. View charts and analytics
4. Export data to CSV or PDF

### Managing Tables and Waiters

1. Go to **Settings** → **Tables** or **Waiters**
2. Add new entries as needed
3. Edit or remove existing entries

## Database Schema

The system uses SQLite with the following tables:

- **users** - System user accounts
- **menu_items** - Food and drink items
- **tables** - Restaurant table numbers
- **waiters** - Staff members
- **orders** - Customer orders
- **order_items** - Individual items in orders
- **payments** - Payment transactions

## Backup and Restore

### Creating Backups

1. Go to **Settings** → **Backup**
2. Enter a backup name
3. Click **Create Backup**
4. The backup file will be downloaded automatically

### Restoring Backups

1. Go to **Settings** → **Backup**
2. Select your backup file
3. Click **Restore Backup**
4. **Warning**: This will overwrite all current data!

## Keyboard Shortcuts

- `Ctrl + N` - New Order
- `Ctrl + D` - Dashboard
- `Ctrl + M` - Menu Management
- `Ctrl + R` - Reports
- `Ctrl + S` - Settings
- `Esc` - Close modals

## Troubleshooting

### Common Issues

**Server won't start:**

- Check if Python is installed: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is available

**Can't access the system:**

- Verify the server is running
- Try accessing `http://127.0.0.1:5000` instead
- Check Windows Firewall settings

**Printer not working:**

- Verify printer is connected and powered on
- Check printer drivers are installed
- Test with a regular document first

**Database errors:**

- The database file `restaurant.db` will be created automatically
- If corrupted, delete the file and restart the application
- Restore from a backup if available

### Performance Optimization

**For older hardware:**

- Close unnecessary browser tabs
- Use Chrome or Edge for better performance
- Disable browser extensions
- Ensure adequate free disk space

**Memory usage:**

- The system uses minimal RAM (~50MB)
- SQLite database is very efficient
- No internet connection required

## Support and Maintenance

### Regular Maintenance

- Create weekly backups of your data
- Monitor disk space usage
- Keep the system updated
- Clean browser cache if performance degrades

### Data Management

- The SQLite database file is located at `restaurant.db`
- Backup files are stored in the `backups/` folder
- Log files (if any) are in the main directory

## Security Notes

- Change the default admin password immediately
- The system is designed for local network use only
- Do not expose the Flask server to the internet
- Regular backups protect against data loss
- User passwords are securely hashed

## License

This Restaurant Cashier Management System is provided as-is for local business use. Modify and adapt as needed for your specific requirements.

---

**Need Help?** Check the troubleshooting section above or review the system logs for error messages.
