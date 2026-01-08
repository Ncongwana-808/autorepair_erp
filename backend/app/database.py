import psycopg
import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")  
DB_NAME = os.getenv("DB_NAME",)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

def close_db_connection(conn):
    """Closes the given database connection."""
    try:
        if conn:
            conn.close()
    except Exception as e:
        print(f"Error closing the database connection: {e}")
        raise