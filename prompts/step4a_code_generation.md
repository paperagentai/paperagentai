Write the complete Python code for experiments/run_experiments.py only.
Do NOT write prompts.py yet — that comes in the next step.

EXPERIMENT DESIGN:
{{03_experiment_design}}

CODE REQUIREMENTS:
- File: experiments/run_experiments.py
- Imports prompt templates from experiments/prompts.py 
  (assume it exists — do not inline prompts here)
- Implements one runner function per experiment defined above
- Calls the LLM APIs specified in the experiment design
- Uses the evaluation tools and metrics defined in the experiment design
- Handles API errors gracefully with retries (max 3 attempts, exponential backoff)
- Prints progress to terminal at each step
- Saves ALL outputs to logs/05_results.md

THE RESULTS LOG (logs/05_results.md) MUST CONTAIN:
- All raw generated output from each model
- All scores and metrics defined in the experiment design
- Failure mode classification for each failed instance
- Aggregate scores per model per language per experiment
- Automatically detected observations and patterns

GENERAL ARCHITECTURE SUGGESTION:
Where the experiment design calls for aesthetic or cultural judgment,
consider a two-model evaluation pattern:
- A generator model produces the output
- A separate evaluator model (different from the generator) assesses it
  against the criteria defined in the experiment design
- The evaluator should return structured output with score AND justification
  — a score without reasoning is not auditable

Only implement this pattern where the experiment design actually requires it.
Do not add it where it is not needed.

Write complete, runnable code.
Do not use placeholders or TODO comments.