# StockAssure

StockAssure is a lightweight, privacy-first, self-hosted inventory management platform designed specifically for bulk shoppers (e.g., Costco, Sam's Club). It abandons the rigid structures of traditional ERP systems, offering a highly intuitive **File-Structure Location Manager** combined with a robust **Modular Plugin Architecture**. 

Whether you are tracking steaks in your garage chest freezer, rotating canned goods in your basement pantry, or organizing gadgets in heavy-duty totes, StockAssure keeps your inventory transparent, extensible, and completely under your control.

---

## ✨ Core Philosophy & Features

### 📁 File-Structure Location Management
No complex terminology like "zones," "aisles," or "bins." StockAssure treats storage exactly like a file system (Windows Explorer or Google Drive):
* **Folders = Locations:** Create infinitely nested spaces. *(e.g., `Garage/` ──► `Chest Freezer #2/` ──► `Bottom Drawer/`)*
* **Files = Objects:** Items live inside these folders. Moving an item is as simple as updating its folder path (Drag & Drop friendly).

### 🔌 Modular Plugin Architecture (Thin Core, Rich Plugins)
To keep the core system blazingly fast and lightweight, the database contains **zero** rigid business-specific columns (like expiry dates, warranty months, or serial numbers). 
* **The Base Object:** The core only knows an item's `id`, `name`, `location_id`, and `template_type`.
* **Plugin-Driven Templates:** External plugins inject custom templates (e.g., `meat_template`, `phone_template`). All custom fields are strictly validated on the backend using **JSON Schema** and stored securely within a single dynamic `extra_data` JSON column. No database migrations will ever be required when installing new plugins.

### 🏠 Built for the Self-Hosted Family
* **Ultra-Lightweight:** Powered by Python (FastAPI) and a single-file SQLite database.
* **100% Privacy:** Your data stays locally on your server. No cloud dependencies.
* **Atomic Concurrency:** Built-in SQLite atomic JSON operations prevent data corruption even if multiple family members update item quantities simultaneously from their phones.
* **PWA Ready:** Designed to work flawlessly as a Progressive Web App, ensuring a snappy, app-like experience when you are down in the basement or out at the grocery store.

---

## 📂 Project Directory Structure (v0.1.0)

StockAssure enforces a strict directory structure to ensure "one-click backup and seamless migration":

```text
stockassure/
├── config/
│   └── stockassure.db       # SQLite Database (Backup this folder to back up everything)
├── plugins/                 # Dynamic Plugin Directory
│   └── cable_manager/        # Example Plugin (plugin_1)
│       ├── plugin_config.json    # Plugin Metadata (ID, version, enabled status)
│       └── templates/       # Folder containing template schemas
│           └── video_cable_template.json
|           └── usb_cable_template.json
|           └── network_cable_template.json 
└── core/                    # FastAPI Backend Source Code

```
## Install and Run StockAssure

### 1. Create and activate a Python virtual environment

#### On macOS / Linux
```bash
cd path/to/stockassure
python3 -m venv .venv
source .venv/bin/activate
```

#### On Windows (PowerShell)
```powershell
cd C:\Users\anthonykwok\Documents\stockassure
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt)
```cmd
cd path/to/stockassure
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install project dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start the backend server
```bash
uvicorn core.main:app --reload
```

### 4. Open the dashboard
Open your browser and go to:

`http://localhost:8000`

### 5. Stop the server
Press `Ctrl+C` in the terminal where the server is running.

### 6. Deactivate the virtual environment
```bash
deactivate
```
