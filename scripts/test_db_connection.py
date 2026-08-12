import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connectors.db_client import get_postgres_connection

def test_connection(profile="readonly"):
    conn = get_postgres_connection(profile)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print(f"{profile} OK:", cur.fetchone())
    finally:
        conn.close()

if __name__ == "__main__":
    test_connection("readonly")
    test_connection("write")