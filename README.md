# HR Onboarding AI Employee

An enterprise-grade, conversational AI Onboarding Assistant powered by **LangChain**, **LangGraph**, **Groq LLM API**, **ChromaDB**, and **SQLite**. It guides newly hired employees through benefits, IT setup, HR policies, security standards, and onboarding checklist management with strict document grounding and multi-turn conversational context.

---

## 🌟 Key Features

1. **Strict HR Document Grounding (RAG)**
   - Answers HR, IT, Benefits, and Security policy questions **only** from verified company onboarding documents.
   - Prohibits hallucinations: explicitly returns `"I couldn't find that information in the provided HR documents, so I don't want to guess."` when queries fall outside the indexed knowledge base.
   - Shows precise source document titles and page numbers (e.g. `Benefits FAQ — Page 2`) with collapsible chunk inspection in the UI.

2. **Persistent Task Management (SQLite)**
   - Thread-safe SQLite backend (`database/onboarding.db`) tracking tasks with statuses (`pending`, `in_progress`, `completed`).
   - Tasks persist across Streamlit reruns, app reloads, and server restarts.
   - Real-time Sidebar with live task metrics and status badges (`✓ Completed`, `○ Pending`, `◐ In-progress`).

3. **Intelligent LangGraph Workflow & State Management**
   - Autonomous intent routing: dynamically branches between HR RAG knowledge retrieval and SQLite task execution.
   - Coreference resolution: seamlessly resolves pronouns and shorthand phrases like `"it"`, `"that task"`, `"the training"`, `"I finished it"`, and `"What do I still need to complete?"`.
   - Ambiguity detection: gracefully asks clarification questions when requests are underspecified (e.g., *"Which training would you like me to add — security training, compliance training, or another training?"*).

4. **Modern, Responsive Streamlit UI**
   - Polished glassmorphism design with custom CSS and typography.
   - Interactive demo suggestion chips for one-click scenario testing.
   - Real-time task sidebar with manual refresh and chat clearing.
   - In-app Groq API key and model selection controls.

---

## 🏗️ Architecture

```
                                    User Input (Streamlit UI)
                                               │
                                               ▼
                                    LangGraph Agent State
                                               │
                           ┌───────────────────┴───────────────────┐
                           │   Intent & Ambiguity Router Node      │
                           │   (Resolves pronouns & checks intent) │
                           └───────────┬───────────────────┬───────┘
                                       │                   │
                  [HR Knowledge Intent]│                   │[Task Action Intent]
                                       ▼                   ▼
                     ┌───────────────────┐       ┌───────────────────┐
                     │ ChromaDB Vector   │       │ SQLite Task Engine│
                     │ Store Retriever   │       │ (CRUD & Disambig) │
                     └─────────┬─────────┘       └─────────┬─────────┘
                               │                           │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │ Response Generator Node       │
                             │ (Grounded Groq LLM Synthesis) │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                               Streamlit UI + Real-time Sidebar
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend UI** | Streamlit (Python) + Custom CSS |
| **Agent Orchestration** | LangGraph & LangChain Core |
| **LLM Inference** | Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) |
| **Vector Database** | ChromaDB |
| **Embeddings** | SentenceTransformers (`all-MiniLM-L6-v2`) via HuggingFace |
| **Task Persistence** | SQLite (`database/onboarding.db`) |
| **PDF Ingestion** | PyMuPDF (`pymupdf`) & PyPDF (`pypdf`) |
| **PDF Generation** | ReportLab |
| **Config & Env** | `python-dotenv` |

---

## 📂 Project Structure

```
hr_onboarding_agent/
│
├── app.py                      # Main Streamlit web application & UI
├── config.py                   # Centralized configuration & environment loader
├── database.py                 # SQLite database layer (CRUD & task search)
├── generate_mock_docs.py       # Script to generate realistic mock HR PDFs
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── .env                        # Local environment configuration
├── README.md                   # Complete documentation
│
├── data/                       # Mock HR PDF documents
│   ├── benefits_faq.pdf        # Health, dental, vision, eligibility, 401(k)
│   ├── it_setup.pdf            # Email, laptop, Cisco VPN, Okta MFA, password policy
│   ├── employee_handbook.pdf   # Working hours, PTO/leave, remote work, code of conduct
│   └── security_policy.pdf     # MFA, password manager, phishing training, incidents
│
├── rag/                        # Retrieval-Augmented Generation module
│   ├── __init__.py
│   ├── loader.py               # PDF loader & recursive character chunker
│   ├── vectorstore.py          # ChromaDB vector store initialization & persistence
│   └── retriever.py            # Similarity search & source citation formatter
│
├── agent/                      # LangGraph Agent workflow module
│   ├── __init__.py
│   ├── state.py                # TypedDict state definition
│   ├── tools.py                # LangChain structured task tools
│   ├── prompts.py              # Strict grounding rules & router prompts
│   └── graph.py                # LangGraph StateGraph pipeline
│
├── database/                   # Persistent storage directory
│   ├── onboarding.db           # SQLite task database
│   └── chroma_db/              # Persistent ChromaDB vector indices
│
└── tests/                      # Automated test suite
    ├── __init__.py
    └── test_agent.py           # Unit and multi-turn integration tests
```

---

## 🚀 Installation & Setup

### 1. Clone or Open the Repository
```bash
cd hr_onboarding_agent
```

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to include your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=all-MiniLM-L6-v2
DATABASE_PATH=database/onboarding.db
CHROMA_DIR=database/chroma_db
DATA_DIR=data
```

*(Note: If you launch without an API key in `.env`, you can also enter your key directly in the Streamlit UI settings sidebar).*

### 5. Generate Mock HR Documents (if not already present)
```bash
python generate_mock_docs.py
```

---

## 🏃 Running the Application

Launch the Streamlit web app:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the test suite covering database operations, RAG grounding, ambiguity handling, and multi-turn coreference resolution:

```bash
python -m unittest tests/test_agent.py
```

---

## 💬 Example Evaluation Conversations

### 1. Core Evaluation Multi-Turn Scenario
```text
User: What do I need to complete before my first day?
AI: Based on the Employee Handbook, before your first day you must:
    • Complete electronic I-9 employment verification
    • Sign your offer letter
    • Submit direct deposit banking details
    
    📄 Source:
    Employee Handbook — Page 2

User: Create a task for the security training.
AI: Done. I've created "Complete security training" with status Pending.

User: What tasks do I have?
AI: Here are your onboarding tasks:
    1. Complete security training — Pending

User: I finished it.
AI: Great. I've marked "Complete security training" as completed.

User: What do I still need to complete?
AI: You currently have no pending onboarding tasks.
```

### 2. Ambiguity Handling
```text
User: Create a task for training.
AI: Which training would you like me to add — security training, compliance training, or another training?

User: Mark training complete. (When multiple training tasks exist)
AI: I found multiple matching tasks ('Complete security training', 'Complete compliance training'). Which one would you like me to mark complete?
```

### 3. Strict Grounding / No Hallucination
```text
User: What is the pet policy for bringing dogs to the office cafeteria?
AI: I couldn't find that information in the provided HR documents, so I don't want to guess.
```

---

## 🔒 Safety & Grounding Principles

1. **No Hallucination**: Company policies, benefits, vacation days, and IT procedures are answered **strictly** from indexed PDFs.
2. **Deterministic Task Execution**: Database updates are executed through parameterized SQLite functions and verified before confirming success to the user.
3. **No Direct SQL Execution**: Arbitrary user SQL is completely blocked.
4. **Data Isolation**: API keys and internal system prompts are protected and never rendered in chat.

---

## 📄 License
MIT License. Created for evaluation purposes.
