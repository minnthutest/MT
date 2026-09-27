# Expense Tracker - Persistent SQL Edition

This version stores your expense data in a persistent SQL database instead of a temporary `/tmp` database.

## Database

### Local mode (default)
The application uses SQLite:

```text
data/expenses.db
```

SQLite is a real SQL database and the file remains on your computer after closing/restarting the app.

### PostgreSQL mode (production/cloud)
Set a `DATABASE_URL` environment variable:

```text
postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME
```

The same application can then use PostgreSQL instead of SQLite.

## Easiest Windows setup

Double-click:

```text
run_app.bat
```

The script automatically:
1. Creates a private `.venv` Python environment.
2. Installs the required packages, including SQLAlchemy.
3. Starts Streamlit.

This prevents the common `ModuleNotFoundError: No module named 'sqlalchemy'` error.

## Manual setup

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run main.py
```

## Existing data

The included `data/expenses.db` contains the migrated database from the previous project. The application automatically creates/migrates the required tables.

## Backup

Run:

```powershell
python backup_database.py
```

Backups are saved in the `backups` folder.

## Important for permanent/cloud use

SQLite is persistent on a local computer, but if you deploy the app to a hosting platform where the filesystem is temporary, use PostgreSQL with persistent storage. Set `DATABASE_URL` on the server and keep regular database backups.
