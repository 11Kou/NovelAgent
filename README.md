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

Start Ollama and make sure the embedding model exists:

```powershell
ollama pull bge-m3
ollama serve
```

Install backend dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the backend:

```powershell
uvicorn app.main:app --reload
```

Run a local smoke check:

```powershell
cd backend
.\.venv\Scripts\python scripts\smoke_check.py
```

The smoke check imports FastAPI, initializes SQLite tables, verifies the DeepSeek missing-key guard, and calls local Ollama `bge-m3` embeddings. It never prints API keys.

Run the frontend once npm is available on PATH:

```powershell
cd frontend
npm install
npm run dev
```

## MVP Flow

1. Enter story idea
2. Draft and confirm story settings
3. Draft and confirm chapter event
4. Generate chapter from assembled context
5. Confirm chapter
6. Memory is extracted and saved immediately
7. Review or correct memory, then continue the next chapter
