from pathlib import Path
from datetime import datetime
import shutil

BASE = Path(__file__).resolve().parent
db = BASE / "data" / "expenses.db"
backup_dir = BASE / "backups"
backup_dir.mkdir(exist_ok=True)

if not db.exists():
    raise SystemExit("No local SQLite database found at data/expenses.db")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target = backup_dir / f"expenses_backup_{stamp}.db"
shutil.copy2(db, target)
print(f"Backup created: {target}")
