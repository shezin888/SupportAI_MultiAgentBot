# SupportAI - Multi-Agent Customer Support Assistant

SupportAI is a Generative AI-powered multi-agent system designed to help customer support executives retrieve customer information and answer questions using company policy documents through a natural-language interface.

The application combines structured customer records from an SQL database with unstructured information from uploaded PDF documents to provide context-aware customer support responses.

## Key Features

- **Multi-Agent Architecture:** Specialized Customer and Policy Agents coordinated by a Supervisor Agent using LangGraph.
- **Natural Language SQL Queries:** Retrieve customer profiles, orders, and support tickets from SQLite through MCP tools.
- **Document-Based RAG:** Upload policy PDFs and retrieve relevant information using semantic search.
- **Persistent Knowledge Base:** Store document embeddings in ChromaDB for future queries without repeated uploads.
- **Context-Aware Conversations:** Resolve follow-up questions using recent conversation history.
- **Multi-Agent Collaboration:** Combine customer records and policy information when a question requires both sources.
- **Grounded Responses:** Generate answers from retrieved information, with source document and page references for policy-related responses.
- **Local LLM:** Run Llama 3.2 and embedding models locally through Ollama without relying on paid LLM APIs.

## System Architecture

SupportAI uses LangGraph to orchestrate the multi-agent workflow. The Supervisor Agent routes incoming questions to the appropriate specialist agent based on the information required.

![SupportAI Architecture](/SupportAI_architecture.png)

### Agent Workflow

| Route | Description |
|-------|-------------|
| CUSTOMER | Retrieves customer profiles, orders, and support-ticket history from SQLite through MCP. |
| POLICY | Retrieves relevant policy information from ChromaDB using RAG. |
| BOTH | Combines customer-specific information with relevant policy information to generate a consolidated response. |
| GENERAL | Handles requests that do not require customer records or policy documents. |

The Contextualizer uses recent conversation history to rewrite follow-up questions into standalone questions before routing.

### Policy Document Ingestion

Uploaded PDF documents are processed through the following pipeline:

```text
PDF Upload
    ↓
PyPDFLoader
    ↓
RecursiveCharacterTextSplitter
    ↓
nomic-embed-text (Ollama)
    ↓
ChromaDB
    ↓
Searchable Policy Knowledge Base
```

When a user asks a policy-related question, the system retrieves relevant document chunks and passes them to the Policy Agent for grounded response generation.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Programming Language | Python |
| User Interface | Streamlit |
| Agent Orchestration | LangGraph |
| LLM | Llama 3.2 3B |
| Local Model Hosting | Ollama |
| Embedding Model | nomic-embed-text |
| Structured Database | SQLite |
| Structured Data Access | Model Context Protocol (MCP) |
| Vector Database | ChromaDB |
| RAG Framework | LangChain |
| PDF Processing | PyPDFLoader |
| Text Chunking | RecursiveCharacterTextSplitter |

## Project Structure

```text
SupportAI_MultiAgentBot/
│
├── agents/
│   ├── customer_agent.py
│   ├── policy_agent.py
│   └── supervisor_agent.py
│
├── database/
│   ├── setup_db.py
│   ├── seed_data.py
│   └── queries.py
│
├── mcp_server/
│   └── server.py
│
├── rag/
│   ├── ingest.py
│   └── retriever.py
│
├── graph/
│   └── workflow.py
│
├── utils/
│   └── ollama_client.py
│
├── data/
│   └── policies/
│
├── assets/
│   └── architecture.png
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/shezin888/SupportAI_MultiAgentBot.git
cd SupportAI-MultiAgentBot
```

### 2. Create a Python Environment

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Ollama

Install Ollama from:

https://ollama.com

Download the required models:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

Ensure the Ollama service is running locally at `http://localhost:11434`.

### 5. Initialize the Customer Database

Create the SQLite database and populate it with synthetic customer data:

```bash
python database/setup_db.py
python database/seed_data.py
```

The database contains sample customer profiles, orders, and support-ticket history.

### 6. Add Policy Documents

Start the application and upload company policy PDFs using the Knowledge Base panel.

Alternatively, place PDF documents in:

```text
data/policies/
```

Then run:

```bash
python rag/ingest.py
```

The documents will be chunked, embedded, and stored in the persistent ChromaDB knowledge base.

### 7. Run the Application

```bash
streamlit run app.py
```

Open the local Streamlit URL displayed in your terminal, usually:

```text
http://localhost:8501
```

The application automatically starts the MCP server when the Customer Agent needs to access structured data.

## Example Questions

### Customer Information

- Give me an overview of Emma Johnson's profile and support tickets.
- What are David Smith's previous orders?
- Show me the latest support ticket for Priya Sharma.

### Policy Information

- What is the current return policy?
- How long is the warranty period for Amazon Renewed products?
- What happens if troubleshooting does not resolve a product issue?

### Combined Customer and Policy Questions

- Based on Emma Johnson's account and the warranty policy, what options are available for her defective headphones?
- Can this customer's recent purchase be returned under the uploaded policy?

### Context-Aware Follow-ups

**User:** Give me Priya Sharma's latest support ticket.

**User:** When was this ticket created?

The system uses recent conversation history to identify the referenced ticket without requiring the customer name or ticket ID to be repeated.

## Data and Limitations

The project uses synthetic customer data for demonstration purposes.

Policy documents are provided by the user and processed locally. The system's policy responses depend on the information available in the uploaded documents.

The application uses locally hosted models through Ollama. Response speed depends on the available system resources.

Customer eligibility for refunds, returns, warranties, or replacements is not assumed when the available records or policy documents do not establish the required conditions.

## Demo

**Demo Video:** [Link](https://drive.google.com/file/d/1Mrq_tfZujqJ8muFJ2dmo3StA_ioBXH9D/view?usp=sharing)
