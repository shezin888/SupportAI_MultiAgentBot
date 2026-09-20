import asyncio
import json
import sys
from pathlib import Path
from textwrap import dedent

from mcp import Client, StdioServerParameters


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.ollama_client import llm


SERVER_PATH = PROJECT_ROOT / "mcp_server" / "server.py"


def parse_mcp_result(result):
    """Convert an MCP tool response into a Python object."""

    if result.structured_content is not None:
        data = result.structured_content

        if isinstance(data, dict) and list(data.keys()) == ["result"]:
            return data["result"]

        return data

    for item in result.content:
        if not hasattr(item, "text"):
            continue

        try:
            return json.loads(item.text)
        except json.JSONDecodeError:
            return item.text

    return None


async def get_customer_data(question):
    """Identify the customer and retrieve their structured records."""

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(PROJECT_ROOT)
    )

    async with Client(server) as client:
        identify_result = await client.call_tool(
            "identify_customer",
            {"question": question}
        )

        customer_match = parse_mcp_result(identify_result)

        if not customer_match or not customer_match.get("found"):
            return {
                "found": False,
                "message": (
                    customer_match.get(
                        "message",
                        "Customer could not be identified."
                    )
                    if isinstance(customer_match, dict)
                    else "Customer could not be identified."
                )
            }

        customer_name = customer_match["name"]

        profile_result = await client.call_tool(
            "get_customer",
            {"name": customer_name}
        )

        orders_result = await client.call_tool(
            "get_orders",
            {"name": customer_name}
        )

        tickets_result = await client.call_tool(
            "get_support_tickets",
            {"name": customer_name}
        )

        return {
            "found": True,
            "customer_name": customer_name,
            "profile": parse_mcp_result(profile_result),
            "orders": parse_mcp_result(orders_result),
            "support_tickets": parse_mcp_result(tickets_result)
        }


async def customer_agent(question):
    """Answer customer-related questions using structured data from MCP."""

    customer_data = await get_customer_data(question)

    if not customer_data.get("found"):
        return customer_data.get(
            "message",
            "Customer could not be identified."
        )

    prompt = dedent(
        f"""
        You are a customer support assistant.

        Answer the question using only the customer records provided below.

        Question:
        {question}

        Customer records:
        {json.dumps(customer_data, indent=2)}

        Guidelines:
        - Answer the question directly and in natural language.
        - Use only facts explicitly present in the records.
        - Never invent, assume, or infer missing customer information.
        - Do not output raw JSON, dictionaries, lists, or database objects.
        - Include only details relevant to the question.
        - If the requested information is unavailable, say that clearly.
        - If asked for the latest order or ticket, use the record with the most recent available date.
        - A ticket's created_at value is its creation date, not its closure date.
        - A Closed status does not tell you when the ticket was closed.
        - Keep the response concise and professional.

        Examples:

        Question: "When was this ticket closed?"
        Response: "The ticket is marked as closed, but the closure date is not available in the customer record."

        Question: "What is the latest order?"
        Response: Summarize the most recent order in a readable sentence.

        Return only the final answer.
        """
    )

    response = llm.invoke(prompt)
    return response.content.strip()


async def main():
    print("\nSupportAI - Customer Agent")

    while True:
        question = input(
            "\nAsk a customer question (or type exit): "
        ).strip()

        if question.lower() in {"exit", "quit"}:
            break

        answer = await customer_agent(question)

        print("\nAssistant:")
        print(answer)


if __name__ == "__main__":
    asyncio.run(main())

