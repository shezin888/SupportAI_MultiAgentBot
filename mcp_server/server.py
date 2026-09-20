import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from mcp.server import MCPServer

from database.queries import (
    get_customer_by_name,
    get_customer_orders,
    get_customer_tickets,
    identify_customer_from_question
)


mcp = MCPServer("SupportAI Customer Data Server")


@mcp.tool()
def identify_customer(question: str) -> dict:
    """
    Return a customer's profile.
    """

    return identify_customer_from_question(question)


@mcp.tool()
def get_customer(name: str) -> dict:
    """
    Retrieve a customer's profile by name.
    """

    customer = get_customer_by_name(name)

    if customer is None:
        return {
            "found": False,
            "message": f"No customer found with name: {name}"
        }

    return {
        "found": True,
        "customer": customer
    }


@mcp.tool()
def get_orders(name: str) -> dict:
    """
    Retrieve all orders belonging to a customer.
    """

    customer = get_customer_by_name(name)

    if customer is None:
        return {
            "found": False,
            "message": f"No customer found with name: {name}"
        }

    orders = get_customer_orders(
        customer["customer_id"]
    )

    return {
        "found": True,
        "customer": customer["name"],
        "orders": orders
    }


@mcp.tool()
def get_support_tickets(name: str) -> dict:
    """
    Retrieve the support-ticket history belonging to a customer.
    """

    customer = get_customer_by_name(name)

    if customer is None:
        return {
            "found": False,
            "message": f"No customer found with name: {name}"
        }

    tickets = get_customer_tickets(
        customer["customer_id"]
    )

    return {
        "found": True,
        "customer": customer["name"],
        "support_tickets": tickets
    }


if __name__ == "__main__":
    mcp.run()