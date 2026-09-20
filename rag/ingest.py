from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = PROJECT_ROOT / "data" / "policies"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "policy_documents"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120
)


def get_vector_store():
    """Return the persistent Chroma policy collection."""

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )


def load_and_chunk_pdf(pdf_path):
    """Load a PDF and split it into chunks for retrieval."""

    pdf_path = Path(pdf_path)

    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()

    chunks = text_splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["source_file"] = pdf_path.name
        chunk.metadata["chunk_id"] = f"{pdf_path.name}_{index}"

    return chunks


def ingest_pdf(pdf_path):
    """Add or replace a PDF in the policy knowledge base."""

    pdf_path = Path(pdf_path)

    chunks = load_and_chunk_pdf(pdf_path)
    vector_store = get_vector_store()

    existing = vector_store.get(
        where={"source_file": pdf_path.name}
    )

    if existing.get("ids"):
        vector_store.delete(
            ids=existing["ids"]
        )

    ids = [
        chunk.metadata["chunk_id"]
        for chunk in chunks
    ]

    vector_store.add_documents(
        documents=chunks,
        ids=ids
    )

    return len(chunks)


def ingest_all_policies():
    """Ingest all PDFs currently stored in the policy directory."""

    POLICY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf_files = sorted(
        POLICY_DIR.glob("*.pdf")
    )

    if not pdf_files:
        print("No policy PDFs found.")
        return

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        count = ingest_pdf(pdf_path)

        print(f"Stored {count} chunks.")

    print("\nKnowledge base updated successfully.")


if __name__ == "__main__":
    ingest_all_policies()