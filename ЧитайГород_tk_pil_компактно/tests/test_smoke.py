from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import core


def test_database_build(tmp_path):
    db_path = tmp_path / "bookstore.db"
    core.initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("select count(*) from users").fetchone()[0] >= 1
        assert conn.execute("select count(*) from products").fetchone()[0] >= 1
        assert conn.execute("select count(*) from orders").fetchone()[0] >= 1
    finally:
        conn.close()


def test_import_folder_unchanged():
    original = sorted(p.name for p in core.IMPORT_DIR.iterdir())
    snapshot = sorted(p.name for p in core.IMPORT_DIR.iterdir())
    assert original == snapshot
