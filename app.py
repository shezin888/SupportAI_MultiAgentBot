import asyncio
from pathlib import Path

import streamlit as st

from graph.workflow import run_support_ai
from rag.ingest import ingest_pdf


PROJECT_ROOT = Path(__file__).resolve().parent
POLICY_DIR = PROJECT_ROOT / "data" / "policies"

POLICY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


st.set_page_config(
    page_title="SupportAI",
    layout="wide"
)

st.title("SupportAI")
st.caption(
    "Generative AI Multi-Agent Customer Support Assistant"
)


with st.sidebar:
    st.header("Knowledge Base")

    st.write(
        "Upload company policy PDFs to add them "
        "to the searchable knowledge base."
    )

    uploaded_file = st.file_uploader(
        "Upload Policy PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:
        if st.button(
            "Add to Knowledge Base",
            use_container_width=True
        ):
            safe_filename = Path(uploaded_file.name).name
            saved_path = POLICY_DIR / safe_filename

            try:
                with st.spinner("Processing policy document..."):
                    with open(saved_path, "wb") as file:
                        file.write(uploaded_file.getbuffer())

                    chunk_count = ingest_pdf(saved_path)

                st.success(
                    f"{safe_filename} added successfully "
                    f"({chunk_count} chunks)"
                )

            except Exception as error:
                st.error(
                    f"Failed to process PDF: {error}"
                )

    st.divider()
    st.subheader("Available Policies")

    policy_files = sorted(
        POLICY_DIR.glob("*.pdf")
    )

    if policy_files:
        for policy in policy_files:
            st.write(policy.name)
    else:
        st.caption(
            "No policy documents uploaded yet."
        )


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi John!\n\n"
                "I'm **SupportAI**. I can help you look up "
                "customer information and answer questions "
                "using company policy documents."
            ),
            "welcome": True
        }
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("route"):
            st.caption(
                f"Agent route: {message['route']}"
            )


question = st.chat_input(
    "Ask about a customer or company policy..."
)


if question:
    recent_history = [
        message
        for message in st.session_state.messages
        if not message.get("welcome", False)
    ][-6:]

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("SupportAI is working..."):
            try:
                result = asyncio.run(
                    run_support_ai(
                        question=question,
                        chat_history=recent_history
                    )
                )

                answer = result.get(
                    "final_answer",
                    "I couldn't generate a response."
                )

                route = result.get(
                    "route",
                    "GENERAL"
                )

                st.markdown(answer)
                st.caption(
                    f"Agent route: {route}"
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "route": route
                    }
                )

            except Exception as error:
                st.error(
                    f"Something went wrong: {error}"
                )