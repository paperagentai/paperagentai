RESEARCH QUESTION:
{{research_question}}

CRITICAL — DOUBLE-BLIND POLICY:
Double-blind means author names and affiliations are omitted.
It does NOT mean hiding experimental details.
Always state explicitly: model names, versions, API parameters,
tools used, evaluation metrics. A reviewer must be able to
reproduce every experiment from what is written.


Write two sections: Methodology (or Task Overview) and Experimental Setup.

PREVIOUSLY WRITTEN SECTIONS:
{{05a_paper}}

EXPERIMENT DESIGN:
{{03_experiment_design}}

INSTRUCTIONS:

## Methodology / Task Overview
- Describe the three experiments clearly and precisely
- For each experiment:
  - The exact task given to the LLM
  - Which languages and meters were tested — name them specifically
  - Which existing tools were used for evaluation — name and cite them
  - The evaluation rubric with scoring criteria
- Name the exact LLM(s) tested with model version and API parameters
  (temperature, max tokens, etc.)
- Include the prompt templates used — verbatim or paraphrased precisely

## Experimental Setup
- Dataset construction — how seeds, meters, and stimuli were selected
- Human or domain-expert evaluation setup where applicable
- Baseline comparisons
- Statistical analysis plan

CONSISTENCY CHECK:
Before writing, read the previously written sections above carefully.
Do not repeat any claims already made. Do not contradict any framing 
already established.

OUTPUT FORMAT:
Valid LaTeX only. No placeholders. No TODO comments.