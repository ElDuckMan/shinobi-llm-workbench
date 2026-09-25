# Facilitator guide — "How an LLM is built, trained, and used"

Audience: mostly software engineers. Slot: 30 minutes. One shared backend you host; participants use their own laptops/phones on the venue wifi.

The app mirrors your talk's arc exactly: **built** (tokenizer) → **trained** (neural net) → **used** (Claude). Send participants the deployed URL at the start.

---

## Run of show (30 min)

**0:00–2:00 — Frame it.** One idea: a language model only ever does one thing — predict the next token. Everything else (chat, code, agents) is that loop plus scale. Today they'll build each piece.

**2:00–9:00 — Built: tokenization (Tab 01).**
- Have everyone open the URL and go to **Tokenize**. Click **Build tokenizer**, then **Tokenize**.
- Point out: text is not fed in as words or letters, it's split into *tokens* by an algorithm that was itself trained. Have them raise the "Merges to learn" slider and rebuild — more merges means common chunks (`tion`, `the·`) collapse into single tokens, so token count drops.
- Have them paste unusual text (a variable name, an emoji, another language) and re-tokenize to see it fragment. Land it: GPT-4-class models do this with ~100k merges. This is why API pricing is per token and why code and rare words cost more.

**9:00–18:00 — Trained: a real neural net (Tab 02).**
- Go to **Train**. Click **Train**. The loss curve drops in a fraction of a second. Explain that this is a genuine neural network learning by gradient descent, just tiny.
- Click **Generate 8 samples**. The output is name-like gibberish. That's the point: a one-layer model with tiny data already captures letter statistics; fluency is what you get when you scale the same recipe up by a billion times.
- Have them change the temperature and resample (low = repetitive, high = chaotic), edit the training data (their own word list) and retrain, and type a letter into the probability box to see the learned distribution over the next character.

**18:00–25:00 — Used: a production model (Tab 03).**
- Go to **Use**. Run the default prompt; it streams token by token — visibly the same next-token loop from Tab 02.
- Have them change the **system prompt** (make it a pirate, a compiler, a code reviewer) and the temperature, and rerun. This is prompt engineering: same model, different behavior from the framing.

**25:00–30:00 — Debrief + takeaway.**
- Tie it together: tokenize → predict next token → sample → repeat. That's the whole machine.
- Takeaway skills: they can now reason about token cost, temperature, and system prompts, and `app.py` is a working template for a streaming Claude-backed web app they can fork for their hackathon project.

---

## The math (for questions, and for rigor)

**Tokenizer (BPE).** Start with the text as a sequence of characters. Repeatedly find the most frequent adjacent pair of symbols and merge it into one new symbol, for a fixed number of merges N. Encoding new text replays the learned merges in order. Vocabulary size = base characters + N merged tokens.

**Neural bigram model (Tab 02).** Let V be the vocabulary size (distinct characters, plus start `^` and end `$`). The model is a single weight matrix `W ∈ ℝ^{V×V}`. For an input character with index `x`, the row `W[x] ∈ ℝ^V` is the vector of logits for the next character. The predicted distribution is the softmax

  `p_j = exp(W[x,j]) / Σ_k exp(W[x,k])`.

Training minimizes the average cross-entropy (negative log-likelihood) over all adjacent character pairs `(x, y)` in the data:

  `L = −(1/N) Σ_n log p_{y_n}`.

The gradient of the loss for one example, with respect to that input's logit row, has the clean closed form

  `∂L/∂W[x,j] = p_j − 1[j = y]`,

averaged over the N examples. Gradient descent updates `W ← W − η · ∂L/∂W` for learning rate η, for the chosen number of epochs. Sampling generates text by starting at `^`, drawing the next character from `softmax(W[x] / T)` where T is the temperature, and repeating until `$`.

This is exactly a one-layer neural language model. Real LLMs replace the single linear layer with a deep transformer and replace single-character context with thousands of tokens of context, but the training objective — predict the next token, minimize cross-entropy — is identical.

**Temperature.** Dividing logits by T before the softmax sharpens (T<1) or flattens (T>1) the distribution. T→0 approaches greedy argmax; higher T raises the chance of low-probability tokens. Anthropic's API accepts T in 0–1.

---

## If something goes wrong

- **Tab 3 shows a deploy note for everyone:** the backend isn't reachable. Check your Render URL loads, and `…/health` returns `ok`. If it returns `no-key`, set `ANTHROPIC_API_KEY`.
- **First request is very slow:** free tier cold start. Warm it before the session by opening the URL.
- **"rate limited":** someone (or the room) exceeded 15 requests/minute per device; wait a few seconds. Adjust `RATE_MAX_REQUESTS` in `app.py` if needed.
- **Wifi drops:** Tabs 01 and 02 keep working offline. Do the tokenizer and training sections, and run Tab 3 yourself as a demo from your own connection.
