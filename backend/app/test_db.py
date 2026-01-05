from database import get_db as get_connection

def test_connection():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database();")
            print("Connected to:", cur.fetchone()[0])

if __name__ == "__main__":
    test_connection()
