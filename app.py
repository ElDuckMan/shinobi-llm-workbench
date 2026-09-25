"""
LLM Workbench — workshop backend.

One tiny FastAPI service that:
  - serves the single-page frontend (index.html) at "/"
  - exposes POST /generate, a streaming proxy to Claude Haiku 4.5
  - rate-limits per client IP so a room full of people can't burn the key

The API key is read from the ANTHROPIC_API_KEY environment variable and
never leaves the server. There is no model download and no PyTorch, so this
runs comfortably on a free tier.
"""

import os
import time
import collections

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import anthropic

MODEL = "claude-haiku-4-5"        # cheapest + fastest current model; streams well
RATE_WINDOW_SEC = 60              # rolling window for the per-IP limit
RATE_MAX_REQUESTS = 15           # requests allowed per IP per window
MAX_TOKENS_CAP = 600             # hard ceiling on output length (cost/time guard)

HERE = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="LLM Workbench")

# Created lazily so the app still boots (and serves the frontend) with no key.
_client = None
def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client

# --- naive in-memory rate limiter (fine for a single-process workshop) ---
_hits = collections.defaultdict(collections.deque)
def rate_limited(ip: str) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and q[0] < now - RATE_WINDOW_SEC:
        q.popleft()
    if len(q) >= RATE_MAX_REQUESTS:
        return True
    q.append(now)
    return False


class GenRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    system: str = Field("", max_length=2000)
    temperature: float = 1.0
    max_tokens: int = 400


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok" if os.environ.get("ANTHROPIC_API_KEY") else "no-key"


@app.post("/generate")
def generate(req: GenRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    if rate_limited(ip):
        return JSONResponse({"error": "rate_limited"}, status_code=429)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return JSONResponse({"error": "no_key"}, status_code=500)

    temperature = min(max(req.temperature, 0.0), 1.0)   # Anthropic range is 0..1
    max_tokens = min(max(req.max_tokens, 1), MAX_TOKENS_CAP)
    system = req.system.strip() or "You are a helpful assistant."

    def stream():
        try:
            with client().messages.stream(
                model=MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": req.prompt}],
            ) as s:
                for chunk in s.text_stream:
                    yield chunk
        except anthropic.APIStatusError as e:
            yield f"\n[api error {e.status_code}]"
        except Exception as e:  # noqa: BLE001 — surface a short, safe message
            yield f"\n[error: {type(e).__name__}]"

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")
