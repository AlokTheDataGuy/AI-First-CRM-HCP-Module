# 🎬 Demo Script — AI-First CRM HCP Log Interaction (10–15 min)

A ready-to-record walkthrough covering the four things the brief asks for:
frontend tour · all 6 LangGraph tools · code explanation · task summary.

---

## Before you hit record (2-min checklist)

- [ ] `docker compose up -d` (Postgres running) and backend `uvicorn` up on :8000
- [ ] Frontend `npm run dev` up on :5173
- [ ] **Avoid the rate limit mid-recording:** record just after your Groq daily quota resets, or temporarily set `GROQ_MODEL=llama-3.1-8b-instant` in `backend/.env` (higher free limit).
- [ ] Allow **microphone** permission in the browser once (for the voice demo).
- [ ] Browser zoom so the form (left) **and** chat (right) are both visible.
- [ ] Open a second terminal ready with: `docker exec -it hcp_crm_db psql -U crm -d hcp_crm`
- [ ] Do one silent dry-run of the prompts below so nothing surprises you on camera.

---

## The prompts (copy/paste ready — fresh scenario)

| Step | Tool | Prompt |
|------|------|--------|
| 1 | `log_interaction` | `Yesterday I had a meeting with Dr. Emily Chen and we went over CardioBoost's efficacy and dosing. She was quite positive. I shared the clinical summary deck and left 2 sample packs. Outcome: she'll trial it with two patients. Follow-up: send the dosing guide and check back in three weeks.` |
| 2 | `edit_interaction` | `Actually that was a video call, not a meeting, and the sentiment was neutral.` |
| 3 | `summarize_notes` (voice) | *(spoken — see script)* |
| 4 | `suggest_followups` | `What follow-up actions do you recommend for this visit?` |
| 5 | `search_hcp` | `Pull up Dr. Sharma from the CRM.` |
| 6 | `save_interaction` | `Great, save this interaction to the database.` |

**Voice-note line to speak (step 3):**
> "So I just wrapped up with Dr. Chen — we spent most of the time on the safety profile. She had concerns about drug interactions in elderly patients, so I walked her through the contraindications. She seemed reassured but wants more data before committing."

---

## Timestamped script

### 0:00 – 1:00 · Intro + what the task is
> "Hi, I'm Alok. This is my AI-First CRM — the **Log HCP Interaction** screen for pharmaceutical field reps. The idea: a rep shouldn't waste selling time typing forms. On the **left** is the structured interaction form; on the **right** is an AI assistant. The key rule from the brief is that I **don't fill the form manually** — I describe the visit in natural language and a **LangGraph agent** powered by **Groq** extracts everything and fills the form for me. It has **six tools**, and I'll demo all of them."

### 1:00 – 2:15 · Frontend walkthrough
- Point out the split-screen, the **Google Inter** font, the form fields (HCP name, type, date/time, attendees, topics, materials, samples, sentiment, outcomes, follow-ups), and the chat panel.
> "Everything's built in **React with Redux Toolkit** — the form and chat share Redux state. When the AI updates a field, you'll see it **flash-highlight**, and the assistant shows a **badge** naming the exact tool it called. Let me show you."

### 2:15 – 3:45 · Tool 1 — `log_interaction`
- Paste **Prompt 1**. Let it fill.
> "One sentence, and watch: it extracted the **HCP name**, resolved **‘yesterday’** to a real date, set the **type**, wrote a professional **Topics Discussed** summary, picked up **positive sentiment**, the **materials**, the **samples**, the **outcome**, and the **follow-up action** — each highlighted. The badge confirms `log_interaction` fired. This tool is doing LLM **entity extraction and summarization**."

### 3:45 – 4:45 · Tool 2 — `edit_interaction`
- Paste **Prompt 2**.
> "Now I made a mistake. Instead of clicking the form, I just tell it. Notice it changed **only** the interaction type to Virtual and the sentiment to Neutral — everything else stayed exactly as it was. That's `edit_interaction`: targeted field updates, not a re-log."

### 4:45 – 6:15 · Tool 3 — `summarize_notes` (voice note)
- Click **🎙 Summarize from Voice Note**. Speak the voice line. Click **⏹ Stop**.
> "This is the voice workflow — and notice the label says **Requires Consent**, because recording an HCP conversation legally requires it. I record, and the audio goes to **Groq's Whisper** model for transcription, then the `summarize_notes` tool condenses it into clean Topics Discussed bullets. So that's a **third Groq model** working with the chat LLM."
- Show the transcribed + summarized result.

### 6:15 – 7:00 · Tool 4 — `suggest_followups`
- Paste **Prompt 4**.
> "I can ask for next steps. `suggest_followups` reads the whole interaction and proposes three concrete actions — you can see them under **AI Suggested Follow-ups**."

### 7:00 – 7:45 · Tool 5 — `search_hcp`
- Paste **Prompt 5**.
> "This one hits the **database**. `search_hcp` looks Dr. Sharma up in Postgres and, since there's a single match, sets it on the form. In a real CRM this pulls from your HCP master list."

### 7:45 – 8:45 · Tool 6 — `save_interaction` + prove it in Postgres
- Paste **Prompt 6**. Then switch to the psql terminal:
  ```sql
  SELECT id, hcp_name, interaction_type, sentiment FROM interactions;
  ```
> "And `save_interaction` writes the record to **PostgreSQL**. Here's the row in the actual database — so the full loop, from spoken/typed input to a persisted CRM record, is real."

### 8:45 – 11:30 · Code walkthrough
Open these files and narrate briefly:
- **`backend/app/agent/graph.py`** — "This is the LangGraph `StateGraph`. It's an `agent → tools → agent` loop: the agent node is the Groq LLM with tools bound; if it calls tools, the `ToolNode` runs them and control comes back for a final reply."
- **`backend/app/agent/tools.py`** — "Here are the six tools. Each is a typed `@tool`; form-mutating ones return a `Command` that patches shared state. `log_interaction` and `edit_interaction` are the two mandatory ones; `summarize_notes` and `suggest_followups` call the LLM themselves; `search_hcp` and `save_interaction` touch Postgres."
- **`backend/app/agent/state.py`** — "The shared state with reducers that merge each tool's field-level deltas."
- **`backend/app/routers/chat.py`** — "Two endpoints: `/api/chat` runs the agent, `/api/transcribe` runs Whisper."
- **`frontend/src/store/`** — "Redux slices: `interactionSlice` holds the form and applies AI updates; `chatSlice` has the `sendMessage` thunk that posts to the backend and dispatches the returned `form_updates`."
- **`frontend/src/components/`** — "`InteractionForm` and `ChatPanel`, plus the `useRecorder` hook for the mic."
> "So the frontend owns the form, sends its snapshot each turn, and the backend returns only what changed."

### 11:30 – 12:45 · Architecture + stack + the model note
> "Stack: **React + Redux**, **FastAPI**, **LangGraph**, **Groq** (Llama 3.3 70B + Whisper), **PostgreSQL**, **Inter** font. One honest note on the LLM: the brief named `gemma2-9b-it`, but **Groq decommissioned that model in October 2025**. The same brief also permits **`llama-3.3-70b-versatile`**, which is active and much better at multi-tool calling — and it's a one-line env change, so any Groq model drops in."

### 12:45 – 14:00 · Task summary (what I understood)
> "To summarize what I took from the task: the goal was an **AI-first** CRM interaction screen where the agent — not manual data entry — drives the form, using **LangGraph** and an **LLM** as mandatory, with at least five tools including Log and Edit. I approached it as a life-science tool: consent-aware voice capture, sentiment, samples, and follow-ups that map to how a real field rep works. The result is six working tools, a persistent database, and a conversational UI that fills and corrects itself. Thanks for watching."

---

## If something misbehaves on camera
- **429 rate limit** → you hit the Groq daily cap; switch to `llama-3.1-8b-instant` and restart, or wait for reset.
- **A field doesn't fill** → just restate it more explicitly; the agent will `edit_interaction` it.
- **Mic won't record** → use the **📝 Paste** button next to the record button and paste the voice line instead.
