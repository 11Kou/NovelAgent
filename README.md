# NovelAgent

NovelAgent is a local MVP for multi-chapter narrative generation with agentic RAG memory.

The first version uses:

- FastAPI backend
- Vue 3 + Vite frontend
- SQLite through SQLModel
- Chroma for vector retrieval
- DeepSeek `deepseek-flash` for text generation
- Local Ollama `bge-m3` for embeddings

Chapter content is stored for reading and export only. It is never embedded. Only natural-language state descriptions are written to Chroma.

## Setup

Copy `.env.example` to `.env` and fill `DEEPSEEK_API_KEY`.

If your local Ollama model is named `bge-m3:latest`, set this in `.env`:

```powershell
OLLAMA_EMBEDDING_MODEL=bge-m3:latest
```

For slower model responses, keep backend and frontend timeouts aligned:

```powershell
MODEL_TIMEOUT_SECONDS=120
MODEL_MAX_RETRIES=1
VITE_API_TIMEOUT_MS=300000
```

When using `scripts\dev_start.py`, backend values are passed to FastAPI and only `VITE_` values are passed to the frontend.

Install backend dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start Ollama and make sure the embedding model exists. If the `ollama` command is on PATH:

```powershell
ollama pull bge-m3
ollama serve
```

If the `ollama` command is not on PATH, start the Ollama desktop app. Then verify models through the backend script:

```powershell
cd backend
.\.venv\Scripts\python scripts\check_ollama.py
```

Run the backend:

```powershell
$env:PYTHONPATH = "."
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Run a local smoke check:

```powershell
cd backend
.\.venv\Scripts\python scripts\smoke_check.py
```

The smoke check imports FastAPI, initializes SQLite tables, verifies the DeepSeek missing-key guard, and calls local Ollama `bge-m3` embeddings. It never prints API keys.

Run the real API smoke after `.env` has `DEEPSEEK_API_KEY`:

```powershell
cd backend
.\.venv\Scripts\python scripts\api_smoke.py
```

The API smoke uses FastAPI's in-process test client to run settings drafting, story creation, chapter event drafting, chapter drafting, chapter confirmation, memory extraction, and LangGraph trace checks.

Run the frontend:

```powershell
cd frontend
pnpm install
pnpm dev --host 127.0.0.1 --port 5173
```

Or start the backend and frontend together from the project root:

```powershell
backend\.venv\Scripts\python scripts\dev_start.py
```

Open `http://127.0.0.1:5173/`.

## Local Verification

Use these checks before a demo:

```powershell
.\scripts\demo_check.ps1
```

This runs the Ollama model check, backend tests, backend compilation, and frontend build. To also run the real DeepSeek API smoke, use:

```powershell
.\scripts\demo_check.ps1 -RunApiSmoke
```

The same checks can also be run manually:

```powershell
$env:PYTHONPATH = "backend"
backend\.venv\Scripts\python -m pytest backend\tests -q
backend\.venv\Scripts\python -m compileall backend\app backend\tests backend\scripts
```

```powershell
cd frontend
pnpm build
```

Optional real model smoke test, after FastAPI dependencies and `.env` are ready:

```powershell
cd backend
.\.venv\Scripts\python scripts\smoke_check.py
.\.venv\Scripts\python scripts\api_smoke.py
```

## MVP Flow

1. Enter story idea
2. Draft and confirm story settings
3. Draft and confirm chapter event
4. Generate chapter from assembled context
5. Confirm chapter
6. Memory is extracted and saved immediately
7. Review or correct memory, then continue the next chapter
