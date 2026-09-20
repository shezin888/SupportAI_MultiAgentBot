import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "customer_support.db"


def create_database():
    """Create the SQLite schema for customer support data."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                membership_tier TEXT,
                location TEXT,
                join_date TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                amount REAL NOT NULL,
                order_date TEXT,
                status TEXT,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                issue_type TEXT,
                description TEXT,
                status TEXT,
                created_at TEXT,
                resolution TEXT,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
            )
            """
        )

    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    create_database()