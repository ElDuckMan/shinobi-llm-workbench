"""LLM Workbench backend: serves index.html and proxies /generate to Claude."""
import os, time, collections
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import anthropic

MODEL = "claude-haiku-4-5"
RATE_WINDOW_SEC = 60
RATE_MAX_REQUESTS = 15
MAX_TOKENS_CAP = 600
HERE = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="LLM Workbench")

_client = None
def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client

_hits = collections.defaultdict(collections.deque)
def rate_limited(ip):
    now = time.time(); q = _hits[ip]
    while q and q[0] < now - RATE_WINDOW_SEC: q.popleft()
    if len(q) >= RATE_MAX_REQUESTS: return True
    q.append(now); return False

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
    temperature = min(max(req.temperature, 0.0), 1.0)
    max_tokens = min(max(req.max_tokens, 1), MAX_TOKENS_CAP)
    system = req.system.strip() or "You are a helpful assistant."
    kwargs = dict(model=MODEL, max_tokens=max_tokens, temperature=temperature,
                  system=system, messages=[{"role": "user", "content": req.prompt}])
    def stream():
        try:
            with client().messages.stream(**kwargs) as s:
                for chunk in s.text_stream:
                    yield chunk
            return
        except anthropic.APIStatusError as e:
            yield f"\n[api error {e.status_code}]"; return
        except Exception:
            try:
                msg = client().messages.create(**kwargs)
                text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
                yield text or "[empty response]"; return
            except Exception as e2:
                yield f"\n[error: {type(e2).__name__}: {e2}]"; return
    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")
