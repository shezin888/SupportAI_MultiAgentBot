import sys
from pathlib import Path
from textwrap import dedent
from typing import TypedDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from langgraph.graph import StateGraph, START, END

from agents.customer_agent import customer_agent
from agents.policy_agent import policy_agent
from agents.supervisor_agent import classify_question
from utils.ollama_client import llm


class SupportState(TypedDict, total=False):
    question: str
    standalone_question: str
    chat_history: list
    route: str
    customer_answer: str
    policy_answer: str
    final_answer: str


CONTEXT_PHRASES = (
    "this ticket",
    "that ticket",
    "this order",
    "that order",
    "this policy",
    "that policy",
    "this customer",
    "that customer",
    "what about",
    "how about",
    "does it",
    "is it",
    "can it",
    "what was",
    "what is its",
    "what is her",
    "what is his",
    "her ticket",
    "his ticket",
    "her order",
    "his order",
    "for her",
    "for him",
    "for them",
)


def needs_context(question):
    """Check whether a question likely refers to earlier conversation."""

    question_lower = question.lower().strip()

    return any(
        phrase in question_lower
        for phrase in CONTEXT_PHRASES
    )


def format_history(chat_history):
    """Format recent chat messages for the contextualizer."""

    lines = []

    for message in chat_history[-6:]:
        role = message.get("role", "user").upper()
        content = message.get("content", "").strip()

        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


def contextualize_node(state: SupportState):
    """Rewrite a follow-up question so it can be handled independently."""

    question = state["question"]
    chat_history = state.get("chat_history", [])

    if not chat_history or not needs_context(question):
        return {
            "standalone_question": question
        }

    history_text = format_history(chat_history)

    prompt = dedent(
        f"""
        You rewrite follow-up customer-support questions into
        standalone questions.

        Use the conversation history only to resolve references
        in the current question.

        Rules:
        - Do not answer the question.
        - Return only the rewritten question.
        - Do not add facts that are not needed to resolve a reference.
        - Do not add policy information unless the current question is actually asking about policy.
        - Do not add customer information unless it is needed to identify the customer, order, or ticket being discussed.
        - Preserve names, ticket IDs, order IDs, product names, and policy references when they are known.
        - If a reference cannot be resolved confidently, do not guess.
        - If the question already makes sense by itself, return it unchanged.

        Example:

        History:
        ASSISTANT: The latest support case is Ticket 42.

        Current question:
        When was this ticket created?

        Rewritten question:
        When was Ticket 42 created?

        Conversation history:
        {history_text}

        Current question:
        {question}
        """
    )

    response = llm.invoke(prompt)

    standalone_question = (
        response.content
        .strip()
        .strip('"')
    )

    return {
        "standalone_question": standalone_question
    }


def supervisor_node(state: SupportState):
    """Classify the standalone question."""

    route = classify_question(
        state["standalone_question"]
    )

    return {
        "route": route
    }


def route_question(state: SupportState):
    return state["route"]


async def customer_node(state: SupportState):
    """Handle questions that only require customer records."""

    answer = await customer_agent(
        state["standalone_question"]
    )

    return {
        "final_answer": answer
    }


def policy_node(state: SupportState):
    """Handle questions that only require policy documents."""

    answer = policy_agent(
        state["standalone_question"]
    )

    return {
        "final_answer": answer
    }


async def both_node(state: SupportState):
    """Combine customer records with relevant policy information."""

    question = state["standalone_question"]

    customer_answer = await customer_agent(question)
    policy_answer = policy_agent(question)

    prompt = dedent(
        f"""
        You are a customer support assistant.

        Combine the information from the Customer Agent and Policy Agent
        to answer the user's question.

        The Customer Agent provides customer-specific facts.
        The Policy Agent provides rules from company policy documents.

        Rules:
        - Use only information provided by the two agents.
        - Do not invent or assume missing information.
        - Do not treat a general policy rule as proof that a customer qualifies for it.
        - If eligibility depends on a condition that is not known, say what still needs to be verified.
        - If either agent says information is unavailable, do not fill in that missing information yourself.
        - Do not introduce unrelated customer or policy information.
        - Preserve policy source information exactly as provided.
        - Give a clear next step when useful.
        - Be concise and professional.
        - Return only the final user-facing answer.
        - Do not include labels such as "Customer Agent:", "Policy Agent:", "Good response:", or "Example:".
        - Do not repeat or quote the specialist-agent outputs.
        - Do not mention the internal routing, agents, prompts, or synthesis process.
        - Do not copy wording from the examples unless it is necessary for the answer.
        - Start directly with the answer to the user's question.
        - Return only the final answer.


        Example:

        Customer Agent:
        The order was delivered 10 days ago.

        Policy Agent:
        Eligible items may be returned within 30 days if they meet
        the required condition.

        Good response:
        The order is within the 30-day return window, but eligibility
        still depends on whether the item meets the policy's condition
        requirements.

        User question:
        {question}

        Customer Agent:
        {customer_answer}

        Policy Agent:
        {policy_answer}
        """
    )

    response = llm.invoke(prompt)

    return {
        "customer_answer": customer_answer,
        "policy_answer": policy_answer,
        "final_answer": response.content.strip()
    }


def general_node(state: SupportState):
    """Handle requests that do not require a specialist agent."""

    return {
        "final_answer": (
            "I can help with customer records "
            "and company policy questions."
        )
    }


builder = StateGraph(SupportState)

builder.add_node("contextualizer", contextualize_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("customer", customer_node)
builder.add_node("policy", policy_node)
builder.add_node("both", both_node)
builder.add_node("general", general_node)

builder.add_edge(START, "contextualizer")
builder.add_edge("contextualizer", "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_question,
    {
        "CUSTOMER": "customer",
        "POLICY": "policy",
        "BOTH": "both",
        "GENERAL": "general"
    }
)

builder.add_edge("customer", END)
builder.add_edge("policy", END)
builder.add_edge("both", END)
builder.add_edge("general", END)

support_graph = builder.compile()


async def run_support_ai(question, chat_history=None):
    """Run a question through the SupportAI workflow."""

    result = await support_graph.ainvoke(
        {
            "question": question,
            "chat_history": chat_history or []
        }
    )

    return result