import re
import sys
from pathlib import Path
from textwrap import dedent


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.retriever import retrieve_policy_context
from utils.ollama_client import llm


NO_POLICY_ANSWER = (
    "The uploaded policy documents do not provide enough "
    "information to answer that question."
)


def remove_duplicates(results):
    """Remove duplicate policy chunks."""

    unique_results = []
    seen = set()

    for result in results:
        key = (
            result.get("source"),
            result.get("page"),
            result.get("content", "").strip()
        )

        if key not in seen:
            seen.add(key)
            unique_results.append(result)

    return unique_results


def build_context(results):
    """
    Label retrieved chunks so the model can reference them
    without generating document names or page numbers itself.
    """

    context_parts = []
    result_map = {}

    for index, result in enumerate(results, start=1):
        context_id = f"C{index}"

        result_map[context_id] = result

        context_parts.append(
            dedent(
                f"""
                [{context_id}]
                Document: {result["source"]}
                Page: {result["page"]}

                {result["content"]}
                """
            ).strip()
        )

    return "\n\n---\n\n".join(context_parts), result_map


def parse_model_response(response_text):
    """
    Separate the final answer from the evidence IDs
    selected by the model.
    """

    parts = re.split(
        r"SOURCE_IDS\s*:",
        response_text,
        maxsplit=1,
        flags=re.IGNORECASE
    )

    answer = re.sub(
        r"^\s*ANSWER\s*:\s*",
        "",
        parts[0],
        flags=re.IGNORECASE
    ).strip()

    source_ids = []

    if len(parts) == 2:
        source_ids = re.findall(
            r"\bC\d+\b",
            parts[1].upper()
        )

    return answer, source_ids


def format_sources(source_ids, result_map):
    """
    Convert evidence IDs into verified document names
    and page numbers.
    """

    sources = []
    seen = set()

    for source_id in source_ids:
        result = result_map.get(source_id)

        if not result:
            continue

        source_info = (
            result["source"],
            result["page"]
        )

        if source_info not in seen:
            seen.add(source_info)
            sources.append(source_info)

    if not sources:
        return ""

    lines = [
        f"- {source}, Page {page}"
        for source, page in sources
    ]

    return "**Source:**\n" + "\n".join(lines)


def policy_agent(question):
    """Answer policy questions using retrieved policy documents."""

    results = retrieve_policy_context(
        question,
        k=6
    )

    results = remove_duplicates(results)

    if not results:
        return NO_POLICY_ANSWER

    context, result_map = build_context(results)

    prompt = f"""
        You are a customer-support policy specialist.

        Your job is to answer the user's question using ONLY the
        policy excerpts provided below.

        IMPORTANT RULES:

        1. Do not use outside knowledge.

        2. Do not invent policy rules, exceptions, eligibility, dates, fees, refund conditions, warranty conditions, or procedures.

        3. Only make a claim if it is clearly supported by one or more of the provided excerpts.

        4. If the uploaded documents do not contain enough information to answer the question, say:

        "The uploaded policy documents do not provide enough information to answer that question."

        5. Do NOT assume that a specific customer qualifies for a refund, warranty, replacement, or return.

        You may explain what the policy says generally.

        Customer-specific eligibility should only be decided when sufficient customer information is available.

        6. If different policy excerpts describe different situations, explain the distinction instead of combining them incorrectly.

        7. Be concise, clear, professional, and user-friendly.

        8. Do not expose your reasoning.

        9. Do not invent document names or page numbers.

        10. At the end, list ONLY the IDs of the excerpts that directly support your answer.

        Use exactly this output format:

        ANSWER:
        <your final answer>

        SOURCE_IDS:
        <C1,C2,...>

        If the answer is unsupported, SOURCE_IDS may be empty.

        User question:
        {question}

        Policy excerpts:

        {context}
        """

    response = llm.invoke(prompt)

    answer, source_ids = parse_model_response(
        response.content.strip()
    )

    if not answer:
        answer = NO_POLICY_ANSWER

    sources = format_sources(
        source_ids,
        result_map
    )

    if sources:
        return f"{answer}\n\n{sources}"

    return answer


def main():
    print("\nSupportAI - Policy Agent")

    while True:
        question = input(
            "\nAsk a policy question (or type exit): "
        ).strip()

        if question.lower() in {"exit", "quit"}:
            break

        answer = policy_agent(question)

        print("\nAssistant:")
        print(answer)


if __name__ == "__main__":
    main()