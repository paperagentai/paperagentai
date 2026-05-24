RESEARCH QUESTION:
{{research_question}}


CRITICAL — DOUBLE-BLIND POLICY:
Double-blind means author names and affiliations are omitted.
It does NOT mean hiding experimental details.
Always state explicitly: model names, versions, API parameters,
tools used, evaluation metrics. A reviewer must be able to
reproduce every experiment from what is written.

Write two sections of the research paper: Related Work and Introduction.
Write Related Work FIRST, then Introduction — so the introduction 
accurately situates the paper against what is known.

LITERATURE REVIEW:
{{01_literature}}

RESEARCH QUESTIONS:
{{02_research_questions}}

EXPERIMENT DESIGN:
{{03_experiment_design}}

INSTRUCTIONS:

## Related Work
- Cover all domains identified in the literature review
- For each paper cited: state what it actually establishes, not just its topic
- Explicitly identify the gaps each body of work leaves open
- End with a paragraph that synthesises all gaps into the specific 
  contribution this paper makes
- Use \paragraph{} for subsections within Related Work
- Cite using \citep{} and \citet{} — include a \section*{References} 
  placeholder at the end listing all citations used in this section

## Introduction
- Open with the broad question driving this paper
- Motivate the chosen domain and method as the diagnostic instrument
- State the three RQs explicitly
- Summarise the key findings (from experiment design — anticipate what experiments test)
- State the contributions clearly as a bulleted list
- Do NOT write the abstract yet — that comes last

OUTPUT FORMAT:
Write valid LaTeX only. Use \section{} and \paragraph{} correctly.
No placeholders. No TODO comments.