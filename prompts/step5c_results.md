RESEARCH QUESTION:
{{research_question}}


CRITICAL — DOUBLE-BLIND POLICY:
Double-blind means author names and affiliations are omitted.
It does NOT mean hiding experimental details.
Always state explicitly: model names, versions, API parameters,
tools used, evaluation metrics. A reviewer must be able to
reproduce every experiment from what is written.

Write the Results section of the paper.

PREVIOUSLY WRITTEN SECTIONS:
{{05a_paper}}
{{05b_paper}}

EXPERIMENTAL RESULTS:
{{05_results}}

INSTRUCTIONS:

## Results
- Report findings for each experiment in order
- Include tables for quantitative results — use \begin{table} with 
  \toprule, \midrule, \bottomrule from booktabs
- For each result state:
  - What was measured
  - What the numbers show
  - What pattern emerges across languages and models
- Report null results as clearly as positive ones — 
  0% metrical validity is a finding, not a failure to report
- Include specific examples of generated output (good and bad) 
  as \begin{quote} or verbatim blocks — concrete examples 
  make abstract claims credible
- Cross-domain comparison: does failure pattern differ across
  the conditions tested — and what does the pattern reveal?
- Do NOT interpret results here — that goes in Discussion

CONSISTENCY CHECK:
Read previously written sections carefully.
Do not repeat claims. Do not contradict established framing.

OUTPUT FORMAT:
Valid LaTeX only. No placeholders. No TODO comments.