# Research Pipeline

An automated pipeline that takes a research question from literature review
through experiment design, code generation, and paper writing.

To use it for a new topic, edit **`prompts/research_question.md`** and
**`context/research_context.md`**, then run. Both files have inline comments
explaining what to change.

---

## Setup

```bash
pip install openai
```

Open `pipeline.py` and set your API key, endpoint, and model at the top:

```python
API_KEY  = os.getenv("LLM_API_KEY", "your_key_here")
BASE_URL = "https://api.deepseek.com"   # any OpenAI-compatible endpoint
MODEL    = "deepseek-v4-pro"
```

Then export your key:

```bash
export LLM_API_KEY="your_key_here"
```

The pipeline uses the OpenAI client, so any OpenAI-compatible API works —
DeepSeek, OpenAI, Together.ai, a local Ollama instance, etc.

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

## How To Run

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
research_pipeline/
├── pipeline.py              ← main script
├── README.md
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
