import re
import sys
from pathlib import Path
from textwrap import dedent


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.queries import identify_customer_from_question
from utils.ollama_client import llm


VALID_ROUTES = {
    "CUSTOMER",
    "POLICY",
    "BOTH",
    "GENERAL"
}


def classify_question(question):
    """Route a user request to the appropriate specialist agent."""

    customer_match = identify_customer_from_question(question)

    customer_reference_found = (
        isinstance(customer_match, dict)
        and customer_match.get("found", False)
    )

    prompt = dedent(
        f"""
        You are the supervisor of a multi-agent customer support system.

        Decide which specialist should handle the user's request.

        Routes:

        CUSTOMER
        Use when the answer requires structured customer records such as:
        - profile or account information
        - orders or purchases
        - support tickets
        - customer history

        POLICY
        Use when the answer requires information from company policy documents, such as:
        - returns or refunds
        - warranties or guarantees
        - replacements
        - fees
        - policy conditions or rules

        BOTH
        Use when the answer requires both customer-specific records and policy information.

        GENERAL
        Use when the request does not require either customer records or company policy documents.

        Examples:

        "Show this customer's recent support tickets."
        -> CUSTOMER

        "What is the current return policy?"
        -> POLICY

        "Based on this customer's order and the return policy, what options are available?"
        -> BOTH

        "What can you help me with?"
        -> GENERAL

        Database signal:
        A known customer, ticket, or order reference was detected:
        {customer_reference_found}

        This signal is only additional context. It does not by itself determine the route.

        User question:
        {question}

        Return only one route:
        CUSTOMER
        POLICY
        BOTH
        GENERAL
        """
    )

    response = llm.invoke(prompt)
    response_text = response.content.strip().upper()

    # Accept the route even if the model adds minor extra formatting.
    match = re.search(
        r"\b(CUSTOMER|POLICY|BOTH|GENERAL)\b",
        response_text
    )

    if match:
        return match.group(1)

    # Safe fallback if the model returns an unusable response.
    if customer_reference_found:
        return "CUSTOMER"

    return "GENERAL"