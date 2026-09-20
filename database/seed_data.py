import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "customer_support.db"


CUSTOMERS = [
    (
        1,
        "Emma Johnson",
        "emma.johnson@test.com",
        "Gold",
        "Toronto",
        "2024-01-15"
    ),
    (
        2,
        "David Smith",
        "david.smith@test.com",
        "Silver",
        "Vancouver",
        "2024-05-20"
    ),
    (
        3,
        "Sarah Lee",
        "sarah.lee@test.com",
        "Gold",
        "Calgary",
        "2023-11-10"
    ),
    (
        4,
        "Michael Brown",
        "michael.brown@test.com",
        "Bronze",
        "Ottawa",
        "2025-02-18"
    ),
    (
        5,
        "Priya Sharma",
        "priya.sharma@test.com",
        "Silver",
        "Montreal",
        "2024-08-03"
    )
]


ORDERS = [
    (
        101,
        1,
        "Wireless Headphones",
        199.99,
        "2026-09-05",
        "Delivered"
    ),
    (
        102,
        1,
        "Mechanical Keyboard",
        129.99,
        "2026-07-15",
        "Delivered"
    ),
    (
        103,
        2,
        "Smart Watch",
        249.99,
        "2026-08-21",
        "Delivered"
    ),
    (
        104,
        3,
        "Bluetooth Speaker",
        89.99,
        "2026-09-01",
        "Delivered"
    ),
    (
        105,
        5,
        "USB-C Dock",
        149.99,
        "2026-08-27",
        "Delivered"
    )
]


SUPPORT_TICKETS = [
    (
        201,
        1,
        "Damaged Product",
        "Wireless headphones arrived with audio cutting out.",
        "Open",
        "2026-09-10",
        None
    ),
    (
        202,
        1,
        "Late Delivery",
        "Mechanical keyboard arrived three days late.",
        "Closed",
        "2026-07-20",
        "Shipping fee refunded."
    ),
    (
        203,
        2,
        "Setup Assistance",
        "Customer needed help pairing the smart watch.",
        "Closed",
        "2026-08-23",
        "Pairing instructions provided."
    ),
    (
        204,
        3,
        "Refund Request",
        "Customer requested a refund for the Bluetooth speaker.",
        "Open",
        "2026-09-04",
        None
    ),
    (
        205,
        5,
        "Missing Accessory",
        "Power adapter was missing from the package.",
        "Closed",
        "2026-08-30",
        "Replacement adapter shipped."
    )
]


def seed_database():
    """Insert sample customer, order, and support-ticket data."""

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.executemany(
            """
            INSERT OR IGNORE INTO customers (
                customer_id,
                name,
                email,
                membership_tier,
                location,
                join_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            CUSTOMERS
        )

        cursor.executemany(
            """
            INSERT OR IGNORE INTO orders (
                order_id,
                customer_id,
                product_name,
                amount,
                order_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ORDERS
        )

        cursor.executemany(
            """
            INSERT OR IGNORE INTO support_tickets (
                ticket_id,
                customer_id,
                issue_type,
                description,
                status,
                created_at,
                resolution
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            SUPPORT_TICKETS
        )

    print("Sample customer data inserted successfully.")


if __name__ == "__main__":
    seed_database()