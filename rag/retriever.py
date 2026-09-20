from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "policy_documents"


embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)


def get_vector_store():
    """Return the persistent Chroma policy collection."""

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )


def retrieve_policy_context(question, k=4):
    """Retrieve the most relevant policy chunks for a question."""

    vector_store = get_vector_store()

    documents = vector_store.similarity_search(
        question,
        k=k
    )

    results = []

    for document in documents:
        page = document.metadata.get("page")

        if page is not None:
            page += 1

        results.append(
            {
                "content": document.page_content,
                "source": document.metadata.get(
                    "source_file",
                    "Unknown"
                ),
                "page": page
            }
        )

    return results


def main():
    print("\nSupportAI - Policy Retriever")

    while True:
        question = input(
            "\nAsk a policy question (or type exit): "
        ).strip()

        if question.lower() in {"exit", "quit"}:
            break

        results = retrieve_policy_context(question)

        print("\nRelevant policy sections:\n")

        for index, result in enumerate(results, start=1):
            print(f"--- Result {index} ---")
            print(f"Source: {result['source']}")
            print(f"Page: {result['page']}")
            print(result["content"])
            print()


if __name__ == "__main__":
    main()