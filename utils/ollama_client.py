from langchain_ollama import ChatOllama


OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "llama3.2:3b"


llm = ChatOllama(
    model=CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
    num_predict=250
)