<div align="center">
  

  <h1>AI-First CRM &mdash; HCP Log Interaction Module</h1>

  <p><strong>An AI-first CRM screen for pharmaceutical field representatives. Reps log Healthcare Professional (HCP) interactions by <em>talking or typing</em> &mdash; a LangGraph agent extracts the details, fills the form, summarizes voice notes, suggests follow-ups, and writes to the database. No manual form-filling.</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Redux-764ABC?logo=redux&logoColor=white" alt="React + Redux"/>
    <img src="https://img.shields.io/badge/Agent-LangGraph-1C3C3C?logo=langchain&logoColor=white" alt="LangGraph"/>
    <img src="https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-F55036?logo=groq&logoColor=white" alt="Groq"/>
    <img src="https://img.shields.io/badge/Speech-Groq%20Whisper-F55036?logo=groq&logoColor=white" alt="Whisper"/>
    <img src="https://img.shields.io/badge/DB-PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="Postgres"/>
    <img src="https://img.shields.io/badge/Tools-6%20LangGraph%20tools-blue" alt="Tools"/>
  </p>

  <sub>Built by <strong>Alok Deep</strong> &middot; Round 1 technical assignment &mdash; AI-First CRM HCP Module.</sub>
</div>

---

## Demo Video

<div align="center">

[![Watch the Demo](https://img.shields.io/badge/%E2%96%B6%20Watch%20the%20Demo-Google%20Drive-EA4335?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1W_TMcLRWbkFFBoZ1IB1lizy_D5e0yzma/view?usp=sharing)

**▶️ [Watch the 10&ndash;15 min walkthrough](https://drive.google.com/file/d/1W_TMcLRWbkFFBoZ1IB1lizy_D5e0yzma/view?usp=sharing)** &mdash; frontend tour, all 6 LangGraph tools live, code structure, and task summary.

</div>

---

## Why This Project

Field reps in pharma waste selling time on data entry &mdash; typing up who they met, what was discussed, what samples they left, and what to do next. This module flips that: the rep **describes the visit in natural language** (typed or spoken) and an **AI agent** does the paperwork.

It is deliberately built the way a real internal tool would be: a **LangGraph** agent orchestrating **six typed tools**, a **FastAPI** backend, a **React + Redux** UI, **Groq** LLM + **Whisper** speech-to-text, and a **PostgreSQL** database &mdash; not a hard-coded demo.

> **The one rule (from the brief):** the rep must **not** fill the left-hand form manually. Every field is populated by the AI assistant on the right, through LangGraph tools driven by an LLM.

---

## What It Does

- 🗣️ **Log by talking or typing** &mdash; _"Today I called Dr. Smith, discussed Product X efficacy, sentiment positive, shared brochures"_ &rarr; the whole form fills itself.
- ✏️ **Correct conversationally** &mdash; _"Actually it was Dr. John, negative, and a meeting not a call"_ &rarr; only those fields change.
- 🎙️ **Voice notes (with consent)** &mdash; record a note &rarr; Groq Whisper transcribes &rarr; the agent summarizes it into Topics Discussed.
- 💡 **Proactive next steps** &mdash; the agent suggests follow-up actions and offers to save.
- 🔎 **HCP lookup** &mdash; searches the CRM database and auto-selects a match.
- 💾 **Persist to the database** &mdash; saves the completed interaction to PostgreSQL.

---

## How This Maps to the Assignment

| Requirement | Where it lives in the project | Status |
|-------------|-------------------------------|:------:|
| Log Interaction screen (form **and** chat) | `frontend/src/components/` &mdash; split-screen `InteractionForm` + `ChatPanel` | ✅ |
| Frontend: **React + Redux** | `frontend/src/store/` &mdash; Redux Toolkit slices (`interaction`, `chat`) | ✅ |
| Backend: **Python + FastAPI** | `backend/app/main.py` + routers | ✅ |
| AI framework: **LangGraph** | `backend/app/agent/graph.py` &mdash; `StateGraph` (agent ↔ ToolNode) | ✅ |
| LLM: **Groq** | `llama-3.3-70b-versatile` (see [LLM note](#a-note-on-the-llm)) | ✅ |
| Database: **MySQL/Postgres** | **PostgreSQL 16** via SQLAlchemy + `docker-compose.yml` | ✅ |
| Font: **Google Inter** | loaded in `frontend/index.html` | ✅ |
| Describe the agent's role | [below](#the-langgraph-agent) | ✅ |
| **≥ 5 tools** incl. Log + Edit | **6 tools** in `backend/app/agent/tools.py` | ✅ |
| README + one repo | this file | ✅ |

---

## The LangGraph Agent

The LangGraph agent is the **orchestration brain** of the screen. It sits between the rep's natural language (typed or spoken) and the structured CRM form. On every message it runs a **`StateGraph`** in an `agent → tools → agent` loop:

1. The **agent node** (Groq LLM with all tools bound) interprets intent and decides which tool(s) to call and with what arguments.
2. The **ToolNode** executes those tools; each returns a `Command` that patches shared state &mdash; the form snapshot and the field-level `form_updates` sent back to the UI.
3. Control returns to the agent to produce a short, natural confirmation.

The **frontend is the source of truth** for the form: each request sends the current form snapshot, and the backend returns only the changed fields, which Redux applies (with a flash-highlight on updated fields).

### The 6 Tools

| # | Tool | Mandatory | What it does | Uses LLM |
|---|------|:---------:|--------------|:--------:|
| 1 | **`log_interaction`** | ✅ | Entity-extracts HCP, date, time, type, sentiment, materials & samples from free text, and writes an elaborated professional Topics Discussed note. | ✅ |
| 2 | **`edit_interaction`** | ✅ | Modifies only the specific field(s) the rep corrects, leaving the rest intact. | ✅ |
| 3 | **`summarize_notes`** | &mdash; | Condenses a raw voice-note transcript / long dictation into clean Topics Discussed bullets. | ✅ |
| 4 | **`suggest_followups`** | &mdash; | Generates 3 actionable next-step recommendations from the current interaction. | ✅ |
| 5 | **`search_hcp`** | &mdash; | Looks up an HCP in the PostgreSQL database and auto-fills a unique match. | &mdash; |
| 6 | **`save_interaction`** | &mdash; | Persists the completed interaction to the `interactions` table. | &mdash; |

> **Bonus AI feature:** recorded voice notes are transcribed by **Groq Whisper** (`whisper-large-v3-turbo`) via `POST /api/transcribe`, then handed to the `summarize_notes` tool &mdash; a third Groq model working alongside the chat LLM.

---

## Architecture

```
+-------------------------------------------------------------+
|                  FRONTEND  (React + Redux)                  |
|                                                             |
|   InteractionForm  <----- Redux store ----->  ChatPanel     |
|   (left: form)        interaction + chat      (right: chat) |
|        ^                  slices                   |        |
|        | form_updates                              | message + form + history
+--------|-------------------------------------------|--------+
         |                                            v
+-------------------------------------------------------------+
|                    BACKEND  (FastAPI)                        |
|   /api/chat        /api/transcribe    /api/interactions      |
|       |                  |                  |  /api/hcps      |
|       v                  v                  v                |
|  +---------------------------+     +----------------------+  |
|  |     LangGraph Agent       |     |   Groq Whisper       |  |
|  |  StateGraph:              |     |  speech -> text      |  |
|  |  agent  <-->  ToolNode    |     +----------------------+  |
|  |    |            |         |                               |
|  |  Groq LLM   6 tools ------+---> patch form / query DB      |
|  +---------------------------+                               |
+----------------------------|--------------------------------+
                             v
                 +-----------------------+
                 |   PostgreSQL 16       |
                 |  hcps · interactions  |
                 +-----------------------+
```

**Design choices worth calling out:**

- **Stateless agent, frontend owns the form.** Each request carries the current form snapshot, so tools like `edit_interaction` know exactly what exists &mdash; no server-side session state to drift.
- **Tools return `Command` objects.** Every tool patches shared graph state cleanly (form + `form_updates` + a tool message), so multiple tools can run in one turn and the reducer merges their deltas.
- **Robust to weaker models.** List fields accept arrays *or* strings *or* `null`; a server-side cleaner drops `"null"`-ish junk &mdash; so tool-call validation never fails on quirky LLM output.
- **Model-agnostic via env.** `GROQ_MODEL` and `GROQ_WHISPER_MODEL` swap models without code changes.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Agent | **LangGraph** | `StateGraph` + `ToolNode` give explicit, debuggable tool orchestration |
| LLM | **Groq &mdash; Llama 3.3 70B** | Fast, reliable multi-tool function calling (see LLM note) |
| Speech | **Groq Whisper** | On-stack voice-note transcription, no extra vendor |
| Backend | **FastAPI + Pydantic** | Async-ready, auto Swagger docs, typed schemas |
| Frontend | **React + Redux Toolkit (Vite)** | Redux for shared form/chat state; Vite for fast HMR |
| Database | **PostgreSQL** (SQLAlchemy) | Meets the SQL requirement; swappable to MySQL/SQLite via `DATABASE_URL` |
| Font | **Google Inter** | Clean, modern UI type |

---

## Quick Start

**Prerequisites:** Python 3.10+ · Node.js 18+ · Docker (for Postgres) · a free [Groq API key](https://console.groq.com/keys)

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

cp .env.example .env              # then paste your GROQ_API_KEY into .env
#  DATABASE_URL is already set for the docker Postgres above
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |

> **No Docker?** Leave `DATABASE_URL` as the default SQLite line in `.env` and skip step 1 &mdash; the app runs with zero database setup. Postgres is recommended to match the assignment's requirement.

---

## Demo Script (all 6 tools in one flow)

1. Type: _"Today I met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochures."_ &rarr; **`log_interaction`**
2. Type: _"Actually the name was Dr. John and the sentiment was negative."_ &rarr; **`edit_interaction`**
3. Click **🎙 Summarize from Voice Note**, speak a quick note &rarr; Whisper + **`summarize_notes`**
4. Type: _"Suggest follow-up actions for this visit."_ &rarr; **`suggest_followups`**
5. Type: _"Find Dr. Sharma in the system."_ &rarr; **`search_hcp`**
6. Type: _"Save this interaction."_ &rarr; **`save_interaction`** (then show the row in Postgres)

---

## Project Structure

```
AI_CRM/
├── backend/                         # FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, startup seed
│   │   ├── config.py                # env settings (Groq key/model, DB url)
│   │   ├── database.py              # SQLAlchemy engine/session
│   │   ├── models.py                # HCP, Interaction tables
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── seed.py                  # sample HCPs
│   │   ├── agent/
│   │   │   ├── graph.py             # StateGraph wiring + run_agent()
│   │   │   ├── tools.py             # the 6 LangGraph tools
│   │   │   ├── state.py             # AgentState + reducers
│   │   │   └── llm.py               # ChatGroq factory
│   │   └── routers/
│   │       ├── chat.py              # /api/chat + /api/transcribe (Whisper)
│   │       └── interactions.py      # CRUD + /api/hcps
│   ├── requirements.txt
│   └── .env.example
├── frontend/                        # React + Redux (Vite)
│   ├── src/
│   │   ├── store/                   # Redux Toolkit slices
│   │   ├── api/client.js
│   │   ├── hooks/useRecorder.js     # MediaRecorder voice capture
│   │   └── components/              # InteractionForm, ChatPanel, ChipList
│   ├── public/
│   │   ├── logo.png                 # ← add your logo
│   │   └── screenshots/             # ← add screenshots + video thumbnail
│   └── package.json
├── docker-compose.yml               # PostgreSQL 16
└── README.md
```

---

## A Note on the LLM

The assignment specified `gemma2-9b-it`, but **Groq decommissioned that model on 2025-10-08** ([deprecations](https://console.groq.com/docs/deprecations)) &mdash; it no longer serves requests. The same brief explicitly permits **`llama-3.3-70b-versatile`**, which is active and far more reliable at multi-tool function calling, so this project uses it by default. The model is fully configurable via `GROQ_MODEL` in `backend/.env` (e.g. `llama-3.1-8b-instant`, Groq's official gemma2 replacement).

---

## Author

**Alok Deep** &mdash; Full-stack developer building toward AI / data roles.

[LinkedIn](https://www.linkedin.com/in/alokthedataguy/) · [Portfolio](https://www.alokthedataguy.in/) · alokdeep9925@gmail.com

---

## License

Educational / assignment project. Not affiliated with any pharmaceutical company. Sample HCP data is synthetic.
