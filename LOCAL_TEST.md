# Run it locally in 2 minutes

## Option A — just look at the features (no setup, no key)
Double-click `index.html`. It opens in your browser.
- Tab 1 (Tokenize) and Tab 2 (Train) work fully — real algorithms, all in the browser.
- Tab 3 (Use) will show a "deploy the backend" note, because live generation needs the server (Option B).

## Option B — full app, including live generation
Requires Python 3.9+ and an Anthropic API key (https://console.anthropic.com).

    pip install -r requirements.txt
    # macOS / Linux:
    export ANTHROPIC_API_KEY=sk-ant-your-key-here
    # Windows PowerShell:
    #   $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
    uvicorn app:app --reload

Then open http://127.0.0.1:8000

Health check: http://127.0.0.1:8000/health  ->  "ok" if the key is set, "no-key" if not.

## What to try
- Tokenize: raise "Merges to learn" and rebuild; paste code or another language and watch it fragment.
- Train: click Train (loss curve drops), Generate 8 samples, change temperature, edit the word list and retrain, type a letter to see its next-char probabilities.
- Use: change the system prompt (make it a compiler, a pirate, a code reviewer) and temperature; watch the reply stream in.

Cost note: Tab 3 uses Claude Haiku 4.5 (~$1 / $5 per million input/output tokens). A prompt + short reply is well under a cent. The backend caps output length and rate-limits per device.
