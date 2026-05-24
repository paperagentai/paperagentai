# PaperAgent — Automated Research Pipeline

An automated pipeline that takes a research question from literature review
through experiment design, code generation, and paper writing.

Two ways to use it:
- **Web UI** — open `https://paperagentai.github.io` in your browser
- **CLI** — run `python pipeline.py --step 1` in the terminal

Both read from the same `prompts/` and `context/` files and write to the
same `logs/` directory, so you can switch between them freely.

---

## Quick Start — Web UI

### 1. Start the backend (on your machine or a server)
```bash
cd paperagentai
pip install openai flask
python webapp/app.py
```
The backend runs on `http://localhost:5000`.

### 2. Open the frontend
Go to **`https://paperagentai.github.io`** (or open `http://localhost:5000` directly).

### 3. Configure
In the **Config** tab:
- **Backend API URL** — `http://localhost:5000` (default; change if backend is elsewhere)
- **API Key** — your LLM provider key
- **LLM Base URL** — `https://api.deepseek.com` (works with any OpenAI-compatible API)
- **Model** — `deepseek-v4-pro` (or any model your provider supports)
- **Research Question** — your central question (one sentence)
- **Research Context** — domain details, venue, experiment constraints, etc.
- Click **Save to Backend**

### 4. Run the pipeline
Go to the **Pipeline** tab, click ▶ Run on any step, or **Run All Steps**.
Output streams token-by-token in real time.

---

## Quick Start — CLI

```bash
pip install openai
export LLM_API_KEY="your_key_here"
python pipeline.py --step 1    # literature review
python pipeline.py --step all  # or run everything at once
```

The pipeline uses the OpenAI client, so any OpenAI-compatible API works —
DeepSeek, OpenAI, Together.ai, a local Ollama instance, etc.
See **[CLI Reference](#cli-reference)** below for all commands.

---

## 🔐 How API Keys Are Handled

| Where | Stored? | Details |
|---|---|---|
| **Browser** (GitHub Pages) | ❌ Not persisted | The key field is a `<input type="password">`. It's only in the tab's memory. Refreshing the page clears it. |
| **Browser localStorage** | ❌ Not stored | Only the Backend API URL is saved in localStorage. The LLM API key is **never** written to localStorage or cookies. |
| **Backend disk** | ❌ Not written | The Flask backend never writes your API key to any file. It only stores it in process memory (`os.environ`) for the lifetime of the server process. |
| **Network** | Sent over HTTPS | When you click Save or Run, the key is sent to your backend. If your backend is on `localhost`, it never leaves your machine. |

**If using the CLI**, export `LLM_API_KEY` in your shell or set it in `pipeline.py` —
that key lives in your shell environment / process memory.

---

## Customizing for a new research idea

**`prompts/research_question.md`** — one sentence, the central question.
This is the anchor for every step in the pipeline.

**`context/research_context.md`** — everything domain-specific:
- Submission venue
- Domains and theoretical frameworks for the literature review
- Experiment constraints (available tools, evaluation approach)
- Code generation notes
- Paper writing and review notes

Optionally add recent papers (post-training-cutoff) to
`context/recent_papers.md` — the pipeline fetches and injects their
content into Step 1 automatically.

---

## CLI Reference

### Run one step at a time (recommended)
```bash
python pipeline.py --step 1    # literature review
python pipeline.py --step 2    # research questions
python pipeline.py --step 3    # experiment design
python pipeline.py --step 4a   # code generation — run_experiments.py
python pipeline.py --step 4b   # code generation — prompts.py
# --- HUMAN STEP: run experiments, fill logs/05_results.md ---
python pipeline.py --step 5a   # write paper — related work + intro
python pipeline.py --step 5b   # write paper — methodology
python pipeline.py --step 5c   # write paper — results
python pipeline.py --step 5d   # write paper — discussion + conclusion + abstract + title
python pipeline.py --step 5e   # review paper — targeted modifications
```

### Run all steps sequentially
```bash
python pipeline.py --step all
```

### Debug mode — prints prompts before calling API
```bash
python pipeline.py --step 1 --debug
```

### Extract a LaTeX template from an Overleaf zip
```bash
python pipeline.py --fetch-template path/to/overleaf.zip
```
Saves the template to `prompts/template.tex`, which Step 5 uses automatically.
Get the zip from Overleaf: Menu → Download → Source.

---

## Folder Structure

```
paperagentai/
├── pipeline.py              ← main CLI script
├── README.md
├── docs/                    ← GitHub Pages frontend (static site)
│   ├── index.html
│   ├── style.css
│   └── script.js
├── webapp/                  ← Flask backend
│   ├── app.py               ← API server (CORS-enabled)
│   ├── templates/
│   └── static/
├── context/
│   ├── research_context.md  ← domain config — EDIT THIS for your topic
│   ├── recent_papers.md     ← papers to inject into literature review
│   └── feedback.txt         ← optional reviewer feedback for Step 5f
├── prompts/
│   ├── research_question.md ← your research question — EDIT THIS
│   ├── system_base.md
│   ├── step1_literature.md … step5e_review.md
│   └── template.tex         ← LaTeX template (see --fetch-template)
├── logs/                    ← all outputs (auto-created)
│   ├── 01_literature.md
│   ├── 02_research_questions.md
│   ├── 03_experiment_design.md
│   ├── 04a_code.md
│   ├── 04b_code.md
│   ├── 05_results.md        ← YOU fill this after running experiments
│   └── 05a_paper.md … 05e_modifications.md
└── experiments/             ← generated code goes here
    ├── run_experiments.py
    └── prompts.py
```

---

## The Human Steps

The pipeline pauses after each step for your review.
There is one step that is entirely human:

**Step 4b (between Step 4 and Step 5):**
1. Extract code from `logs/04a_code.md` and `logs/04b_code.md`
2. Save to `experiments/run_experiments.py` and `experiments/prompts.py`
3. Install required libraries
4. Run the experiments
5. Save all results to `logs/05_results.md`

Format for `logs/05_results.md`:
```markdown
# Experimental Results

## Experiment 1 — [description]
### Model: Claude / Condition: [X]
[raw output]
- Score metric A: X/10
- Score metric B: X/10
- Failure mode: [description]

## Experiment 2 — [description]
...
```

---

## Submission

Set your venue and submission link in `context/research_context.md`
under the **Submission Venue** section.
