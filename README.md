# LLM Workbench — OwlHacks 2026

A tiny web app for a 30-minute workshop on how a language model is **built, trained, and used**. Three browser tabs:

1. **Tokenize** — build a real byte-pair-encoding tokenizer from a corpus, then tokenize text. Runs entirely in the browser.
2. **Train** — train a real one-layer neural network (a bigram language model) by gradient descent. Watch the loss fall, then sample from it. Runs entirely in the browser.
3. **Use** — send a prompt to **Claude Haiku 4.5** through this backend and stream the reply. This is the only tab that needs the server.

Because tabs 1 and 2 run client-side, the workshop keeps working even if the venue wifi hiccups. Only tab 3 touches the network, and it fails gracefully with an on-screen message if the backend isn't reachable.

---

## What you need

- An Anthropic API key: https://console.anthropic.com → API Keys.
- A free Render account (or any host that runs Python). Render is the path below.

Cost is small. Claude Haiku 4.5 is about **$1 per million input tokens and $5 per million output tokens**. A workshop prompt plus a 400-token reply is well under a cent. The backend also rate-limits each device to 15 requests/minute, and caps replies at 600 tokens, so a room can't run up a surprise bill. Set a spend limit in the Anthropic console for peace of mind.

---

## Deploy to Render (about 5 minutes)

1. Put these files in a GitHub repo (or use "Deploy from a public repo").
2. In Render, click **New → Web Service** and point it at the repo.
3. Render reads `render.yaml` and fills in the settings. If entering them by hand instead:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. Under **Environment**, add a variable:
   - Key: `ANTHROPIC_API_KEY`  Value: your key
5. Click **Create Web Service**. When it goes live you'll get a URL like `https://llm-workshop.onrender.com`. That URL is what participants open.

**Before the session:** the free tier sleeps after ~15 minutes idle, and the first hit then takes ~30–50 seconds to wake. Open your URL once a couple of minutes before you start so it's warm. Check `https://YOUR-URL/health` — it returns `ok` when the key is set, `no-key` if it isn't.

---

## Run locally (for testing)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...     # Windows: set ANTHROPIC_API_KEY=...
uvicorn app:app --reload
# open http://127.0.0.1:8000
```

You can also just double-click `index.html` to try tabs 1 and 2 with no server at all; tab 3 will show its deploy note.

---

## Files

- `index.html` — the whole frontend (no build step, no framework).
- `app.py` — FastAPI backend: serves the page, streams `/generate`, rate-limits.
- `requirements.txt`, `render.yaml`, `.env.example`, `.gitignore`.
- `FACILITATOR.md` — the run-of-show and the math behind each tab.

## Security notes

- The API key stays on the server, read from `ANTHROPIC_API_KEY`. It is never sent to the browser.
- `/generate` validates input length, caps `max_tokens`, clamps temperature to 0–1, and rate-limits per IP.
- To harden further for a public link, lower `RATE_MAX_REQUESTS` in `app.py` or add a shared passphrase check.
