import re
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "customer_support.db"


def get_connection():
    """Create a SQLite connection that returns rows as dictionaries."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_customer_by_name(name):
    """Return a customer whose full name matches the given name."""

    with get_connection() as conn:
        customer = conn.execute(
            """
            SELECT *
            FROM customers
            WHERE LOWER(name) = LOWER(?)
            """,
            (name,)
        ).fetchone()

    return dict(customer) if customer else None


def get_customer_orders(customer_id):
    """Return a customer's orders, newest first."""

    with get_connection() as conn:
        orders = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE customer_id = ?
            ORDER BY order_date DESC
            """,
            (customer_id,)
        ).fetchall()

    return [dict(order) for order in orders]


def get_customer_tickets(customer_id):
    """Return a customer's support tickets, newest first."""

    with get_connection() as conn:
        tickets = conn.execute(
            """
            SELECT *
            FROM support_tickets
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,)
        ).fetchall()

    return [dict(ticket) for ticket in tickets]


def identify_customer_from_question(question):
    """
    Identify a customer using a full name, unique first name,
    ticket ID, or order ID found in the question.
    """

    question_lower = question.lower().strip()

    with get_connection() as conn:
        customers = conn.execute(
            """
            SELECT customer_id, name
            FROM customers
            """
        ).fetchall()

        # Try an exact full-name reference first.
        for customer in customers:
            if customer["name"].lower() in question_lower:
                return {
                    "found": True,
                    "customer_id": customer["customer_id"],
                    "name": customer["name"]
                }

        # Allow first names only when they identify one customer.
        first_name_matches = []

        for customer in customers:
            first_name = customer["name"].split()[0].lower()

            if re.search(
                rf"\b{re.escape(first_name)}\b",
                question_lower
            ):
                first_name_matches.append(customer)

        if len(first_name_matches) == 1:
            customer = first_name_matches[0]

            return {
                "found": True,
                "customer_id": customer["customer_id"],
                "name": customer["name"]
            }

        # Try a support ticket reference.
        ticket_match = re.search(
            r"\bticket(?:\s+(?:id|number|no\.?))?\s*[:#-]?\s*(\d+)\b",
            question_lower
        )

        if ticket_match:
            ticket_id = int(ticket_match.group(1))

            customer = conn.execute(
                """
                SELECT c.customer_id, c.name
                FROM support_tickets AS t
                JOIN customers AS c
                    ON t.customer_id = c.customer_id
                WHERE t.ticket_id = ?
                """,
                (ticket_id,)
            ).fetchone()

            if customer:
                return {
                    "found": True,
                    "customer_id": customer["customer_id"],
                    "name": customer["name"]
                }

        # Try an order reference.
        order_match = re.search(
            r"\border(?:\s+(?:id|number|no\.?))?\s*[:#-]?\s*(\d+)\b",
            question_lower
        )

        if order_match:
            order_id = int(order_match.group(1))

            customer = conn.execute(
                """
                SELECT c.customer_id, c.name
                FROM orders AS o
                JOIN customers AS c
                    ON o.customer_id = c.customer_id
                WHERE o.order_id = ?
                """,
                (order_id,)
            ).fetchone()

            if customer:
                return {
                    "found": True,
                    "customer_id": customer["customer_id"],
                    "name": customer["name"]
                }

    return {
        "found": False,
        "message": "No matching customer was found."
    }