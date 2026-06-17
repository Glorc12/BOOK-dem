from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core import initialize_database


if __name__ == "__main__":
    path = initialize_database()
    print(f"Database created: {path}")
