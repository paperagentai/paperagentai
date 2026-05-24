"""
Research Pipeline

Edit prompts/research_question.md and context/research_context.md
for your topic, then run.

Workflow:
  Step 1 → Literature Review
  Step 2 → Research Questions
  Step 3 → Experiment Design
  Step 4 → Code Generation
  Step 4b→ [HUMAN] Run experiments, save results to logs/05_results.md
  Step 5 → Write Paper

Usage:
  python pipeline.py --step 1          # run a specific step
  python pipeline.py --step all        # run all steps sequentially
  python pipeline.py --step 1 --debug  # print prompts before calling API
"""

import os
import sys
import argparse
import zipfile
import io
from datetime import datetime
from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────────

API_KEY  = os.getenv("LLM_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.deepseek.com"
MODEL    = "deepseek-v4-pro"

# Max output tokens per step — different steps need different limits
STEP_MAX_TOKENS = {
    "1":  32000,  # Literature review — deep multi-domain coverage
    "2":  8000,   # Research questions — focused output
    "3":  16000,  # Experiment design — detailed spec
    "4":  32000,  # Code generation — shared limit for 4a and 4b
    "4a": 32000,  # Code generation — run_experiments.py
    "4b": 16000,  # Code generation — prompts.py
    "5a": 128000,  # Related Work + Introduction
    "5b": 128000,  # Methodology + Experimental Setup
    "5c": 128000,  # Results
    "5d": 128000,  # Discussion + Conclusion + Abstract
    "5e": 32000,   # Review — modifications only, not full regeneration
}

PROMPT_DIR   = "prompts"
LOG_DIR      = "logs"
RESULTS_FILE = f"{LOG_DIR}/05_results.md"   # human fills this

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def load_research_question() -> str:
    """Load the central research question — single source of truth."""
    path = f"{PROMPT_DIR}/research_question.md"
    if not os.path.exists(path):
        print(f"  [ERROR] research_question.md not found in {PROMPT_DIR}/")
        sys.exit(1)
    with open(path, "r") as f:
        return f.read().strip()

RESEARCH_QUESTION = load_research_question()

def load_research_context() -> str:
    """Load domain-specific context from context/research_context.md."""
    path = "context/research_context.md"
    if not os.path.exists(path):
        return "(none provided — add domain context to context/research_context.md)"
    with open(path, "r") as f:
        return f.read().strip()

RESEARCH_CONTEXT = load_research_context()

# ── File Helpers ───────────────────────────────────────────────────────────────

def fetch_template(zip_path: str):
    """Extract LaTeX template from Overleaf zip and save to prompts/template.tex.

    HOW TO GET THE ZIP:
      1. Open https://www.overleaf.com/read/tyqznhpcmjpp
      2. Menu (top left) → Download → Source (.zip)
      3. Run: python pipeline.py --fetch-template path/to/downloaded.zip
    """
    if not os.path.exists(zip_path):
        print(f"  [ERROR] Zip file not found: {zip_path}")
        sys.exit(1)

    print(f"  [TEMPLATE] Reading zip: {zip_path}")
    combined = []

    with zipfile.ZipFile(zip_path, "r") as z:
        tex_files = [f for f in z.namelist() if f.endswith(".tex")]
        print(f"  [TEMPLATE] Found .tex files: {tex_files}")

        # Main file first, then others
        main_files = [f for f in tex_files if "main" in f.lower()]
        other_files = [f for f in tex_files if f not in main_files]

        for filename in main_files + other_files:
            content = z.read(filename).decode("utf-8", errors="ignore")
            combined.append(f"% ── FILE: {filename} ──────────────────────\n")
            combined.append(content)
            combined.append("\n\n")

    if not combined:
        print("  [ERROR] No .tex files found in zip.")
        sys.exit(1)

    os.makedirs(PROMPT_DIR, exist_ok=True)
    out_path = f"{PROMPT_DIR}/template.tex"
    with open(out_path, "w") as f:
        f.write("".join(combined))

    print(f"  [SAVED] Template extracted to {out_path}")
    print("  You can now run Step 5 — the template will be used automatically.")


def load_template() -> str:
    """Load the LaTeX template. Warns clearly if not yet fetched."""
    path = f"{PROMPT_DIR}/template.tex"
    if not os.path.exists(path):
        print("  [ERROR] Template not found at prompts/template.tex")
        print("  Run first: python pipeline.py --fetch-template path/to/overleaf.zip")
        print("  Get the zip from: Menu → Download → Source at https://www.overleaf.com/read/tyqznhpcmjpp")
        sys.exit(1)
    with open(path, "r") as f:
        return f.read()


def fetch_url_content(url: str) -> str:
    """Fetch the text content of a URL. Handles HTML and PDF."""
    import urllib.request
    import urllib.error

    print(f"  [FETCH] {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (research pipeline)"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            content_type = r.headers.get("Content-Type", "")
            raw = r.read()

        # PDF — extract text using pdfminer if available, else note it
        if "pdf" in content_type or url.lower().endswith(".pdf"):
            try:
                from pdfminer.high_level import extract_text_to_fp
                from pdfminer.layout import LAParams
                import io as _io
                out = _io.StringIO()
                extract_text_to_fp(_io.BytesIO(raw), out, laparams=LAParams())
                text = out.getvalue().strip()
                return text[:12000]  # cap at 12K chars per paper
            except ImportError:
                return f"[PDF detected but pdfminer not installed. Run: pip install pdfminer.six]\nURL: {url}"

        # HTML — strip tags simply
        html = raw.decode("utf-8", errors="ignore")
        # Remove script/style blocks
        import re
        html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", html, flags=re.DOTALL)
        # Remove all tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text[:12000]  # cap at 12K chars per paper

    except urllib.error.HTTPError as e:
        return f"[Could not fetch — HTTP {e.code}: {url}]"
    except Exception as e:
        return f"[Could not fetch — {e}: {url}]"


def load_recent_papers() -> str:
    """Load human-curated recent papers from context/recent_papers.md.
    Automatically fetches and injects content for each URL found."""
    path = "context/recent_papers.md"
    if not os.path.exists(path):
        return "(none provided)"

    with open(path, "r") as f:
        raw = f.read()

    # Check if any titles have been filled in
    import re
    titles = re.findall(r"\*\*Title:\*\*\s*(.+)", raw)
    titles = [t.strip() for t in titles if t.strip()]
    if not titles:
        return "(none provided — add papers to context/recent_papers.md)"

    # Parse each paper block
    blocks = re.split(r"^## Paper \d+", raw, flags=re.MULTILINE)
    output_sections = []

    for block in blocks:
        if not block.strip() or block.strip().startswith("#"):
            continue

        title_match = re.search(r"\*\*Title:\*\*\s*(.+)", block)
        url_match   = re.search(r"\*\*URL:\*\*\s*(\S+)", block)

        title = title_match.group(1).strip() if title_match else "Untitled"
        url   = url_match.group(1).strip()   if url_match   else ""

        if not title or title == "Untitled":
            continue

        section = [f"### {title}"]
        if url:
            section.append(f"Source: {url}")
            fetched = fetch_url_content(url)
            section.append(f"\nContent:\n{fetched}")
        else:
            section.append("(no URL provided)")

        output_sections.append("\n".join(section))

    if not output_sections:
        return "(none provided — fill in titles and URLs in context/recent_papers.md)"

    return "\n\n---\n\n".join(output_sections)


def read_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ folder."""
    path = f"{PROMPT_DIR}/{filename}"
    if not os.path.exists(path):
        print(f"  [ERROR] Prompt file not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        return f.read()

def read_log(filename: str) -> str:
    """Load a log file. Returns empty string with warning if missing."""
    path = f"{LOG_DIR}/{filename}"
    if not os.path.exists(path):
        print(f"  [WARN] Log not found: {path}")
        return ""
    with open(path, "r") as f:
        return f.read()

def write_log(filename: str, content: str):
    """Save output to a log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    path = f"{LOG_DIR}/{filename}"
    with open(path, "w") as f:
        f.write(content)
    print(f"  [SAVED] {path}")

def fill_template(template: str, variables: dict) -> str:
    """Replace {{key}} placeholders in a prompt template with log content.
    {{research_question}} is always available in every prompt automatically."""
    all_vars = {"research_question": RESEARCH_QUESTION, "research_context": RESEARCH_CONTEXT, **variables}
    for key, value in all_vars.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template

# ── API ────────────────────────────────────────────────────────────────────────

def call_api(system_prompt: str, user_prompt: str, debug: bool = False, max_tokens: int = 8000) -> str:
    if debug:
        print("\n── SYSTEM PROMPT ──────────────────────────────────────")
        print(system_prompt)
        print("\n── USER PROMPT ────────────────────────────────────────")
        print(user_prompt)
        print("───────────────────────────────────────────────────────\n")

    print(f"  [API] Calling {MODEL}... (this may take a minute)")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        # Note: temperature not set — deepseek-v4-pro uses thinking mode
        # by default which handles reasoning internally
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
    )
    return response.choices[0].message.content

# ── Flow Control ───────────────────────────────────────────────────────────────

def header(step, title: str):
    print(f"\n{'='*60}")
    print(f"  STEP {step}: {title}")
    print(f"{'='*60}")

def pause_for_review(log_file: str):
    print(f"\n  [REVIEW] Output saved to logs/{log_file}")
    print("  Open the file, review it, edit if needed,")
    print("  then press Enter to continue — or type 'skip' to stop.")
    response = input("  > ").strip().lower()
    if response == "skip":
        print("  Pipeline paused. Re-run with --step <next_step> when ready.")
        sys.exit(0)

def run_step(step_num, title: str, prompt_file: str,
             log_out: str, variables: dict, debug: bool, max_tokens: int = 8000, note: str = ""):

    header(step_num, title)

    system = fill_template(read_prompt("system_base.md"), variables)
    user   = fill_template(read_prompt(prompt_file), variables)

    output = call_api(system, user, debug, max_tokens)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_content = f"# Step {step_num}: {title}\n_Generated: {timestamp}_\n\n{output}"
    write_log(log_out, log_content)

    if note:
        print(f"\n  [NOTE] {note}")

    pause_for_review(log_out)

# ── Steps ──────────────────────────────────────────────────────────────────────

def step1(debug): run_step(
    step_num    = 1,
    title       = "Literature Review",
    prompt_file = "step1_literature.md",
    log_out     = "01_literature.md",
    variables   = {"recent_papers": load_recent_papers()},
    debug       = debug,
    max_tokens  = STEP_MAX_TOKENS["1"],
)

def step2(debug): run_step(
    step_num    = 2,
    title       = "Research Questions",
    prompt_file = "step2_research_questions.md",
    log_out     = "02_research_questions.md",
    variables   = {"01_literature": read_log("01_literature.md")},
    debug       = debug,
    max_tokens  = STEP_MAX_TOKENS["2"],
)

def step3(debug): run_step(
    step_num    = 3,
    title       = "Experiment Design",
    prompt_file = "step3_experiment_design.md",
    log_out     = "03_experiment_design.md",
    variables   = {
        "01_literature":         read_log("01_literature.md"),
        "02_research_questions": read_log("02_research_questions.md"),
    },
    debug      = debug,
    max_tokens = STEP_MAX_TOKENS["3"],
)

def step4a(debug): run_step(
    step_num    = "4a",
    title       = "Code Generation — run_experiments.py",
    prompt_file = "step4a_code_generation.md",
    log_out     = "04a_code.md",
    variables   = {"03_experiment_design": read_log("03_experiment_design.md")},
    debug       = debug,
    max_tokens  = STEP_MAX_TOKENS["4a"],
    note        = "Extract run_experiments.py from logs/04a_code.md → save to experiments/run_experiments.py",
)

def step4b(debug): run_step(
    step_num    = "4b",
    title       = "Code Generation — prompts.py",
    prompt_file = "step4b_prompts.md",
    log_out     = "04b_code.md",
    variables   = {"04a_code": read_log("04a_code.md")},
    debug       = debug,
    max_tokens  = STEP_MAX_TOKENS["4b"],
    note        = (
        "Extract prompts.py from logs/04b_code.md → save to experiments/prompts.py\n"
        "  Install required libraries, run experiments, save results to logs/05_results.md"
    ),
)

def _require_results():
    if not os.path.exists(RESULTS_FILE):
        print(f"\n  [ERROR] Results file not found: {RESULTS_FILE}")
        print("  Complete Step 4b first: run experiments and save results.")
        sys.exit(1)

def _require_log(filename: str, reason: str):
    """Block if a required log file from a previous step is missing."""
    path = f"{LOG_DIR}/{filename}"
    if not os.path.exists(path):
        print(f"\n  [ERROR] Required log not found: {path}")
        print(f"  {reason}")
        sys.exit(1)

def step5a(debug):
    run_step(
        step_num    = "5a",
        title       = "Write Paper — Related Work + Introduction",
        prompt_file = "step5a_related_work_intro.md",
        log_out     = "05a_paper.md",
        variables   = {
            "01_literature":         read_log("01_literature.md"),
            "02_research_questions": read_log("02_research_questions.md"),
            "03_experiment_design":  read_log("03_experiment_design.md"),
        },
        debug      = debug,
        max_tokens = STEP_MAX_TOKENS["5a"],
    )

def step5b(debug):
    run_step(
        step_num    = "5b",
        title       = "Write Paper — Methodology + Experimental Setup",
        prompt_file = "step5b_methodology.md",
        log_out     = "05b_paper.md",
        variables   = {
            "02_research_questions": read_log("02_research_questions.md"),
            "03_experiment_design":  read_log("03_experiment_design.md"),
            "05a_paper":             read_log("05a_paper.md"),
        },
        debug      = debug,
        max_tokens = STEP_MAX_TOKENS["5b"],
    )

def step5c(debug):
    _require_results()
    run_step(
        step_num    = "5c",
        title       = "Write Paper — Results",
        prompt_file = "step5c_results.md",
        log_out     = "05c_paper.md",
        variables   = {
            "05_results": read_log("05_results.md"),
            "05a_paper":  read_log("05a_paper.md"),
            "05b_paper":  read_log("05b_paper.md"),
        },
        debug      = debug,
        max_tokens = STEP_MAX_TOKENS["5c"],
    )

def step5d(debug):
    _require_results()
    run_step(
        step_num    = "5d",
        title       = "Write Paper — Discussion + Conclusion + Abstract",
        prompt_file = "step5d_discussion_conclusion.md",
        log_out     = "05d_paper.md",
        variables   = {
            "05a_paper": read_log("05a_paper.md"),
            "05b_paper": read_log("05b_paper.md"),
            "05c_paper": read_log("05c_paper.md"),
        },
        debug      = debug,
        max_tokens = STEP_MAX_TOKENS["5d"],
    )

def step5e(debug):
    _require_log("05d_paper.md", "Step 5d must complete first.")
    run_step(
        step_num    = "5e",
        title       = "Review Paper — Targeted Modifications Only",
        prompt_file = "step5e_review.md",
        log_out     = "05e_modifications.md",
        variables   = {
            "05a_paper": read_log("05a_paper.md"),
            "05b_paper": read_log("05b_paper.md"),
            "05c_paper": read_log("05c_paper.md"),
            "05d_paper": read_log("05d_paper.md"),
        },
        debug      = debug,
        max_tokens = STEP_MAX_TOKENS["5e"],
        note       = (
            "Apply modifications from logs/05e_modifications.md manually\n"
            "  Assemble final paper from 05a-05d sections"
        ),
    )

# ── Main ───────────────────────────────────────────────────────────────────────

STEPS = {
    "1":  step1,
    "2":  step2,
    "3":  step3,
    "4a": step4a,
    "4b": step4b,
    "5a": step5a,
    "5b": step5b,
    "5c": step5c,
    "5d": step5d,
    "5e": step5e,
}

def main():
    parser = argparse.ArgumentParser(description="Research Pipeline")
    parser.add_argument("--step",  default=None,
                        help="Step to run: 1, 2, 3, 4a, 4b, 5a, 5b, 5c, 5d, 5e, or 'all'")
    parser.add_argument("--fetch-template", metavar="ZIP_PATH",
                        help="Extract Overleaf template zip to prompts/template.tex")
    parser.add_argument("--debug", action="store_true",
                        help="Print prompts before calling API")
    args = parser.parse_args()

    # Handle --fetch-template independently of --step
    if args.fetch_template:
        fetch_template(args.fetch_template)
        sys.exit(0)

    if not args.step:
        parser.print_help()
        sys.exit(1)

    steps_to_run = list(STEPS.keys()) if args.step == "all" else [args.step]

    if any(s not in STEPS for s in steps_to_run):
        print(f"Unknown step: {args.step}. Choose from: 1 2 3 4a 4b 5a 5b 5c 5d 5e all")
        sys.exit(1)

    print(f"\nResearch Pipeline")
    print(f"Model  : {MODEL}")
    print(f"API    : {BASE_URL}")
    print(f"Steps  : {', '.join(steps_to_run)}")

    for step_key in steps_to_run:
        STEPS[step_key](args.debug)

    print("\n  Pipeline complete.\n")

if __name__ == "__main__":
    main()