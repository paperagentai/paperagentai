# Research Context

This file is injected as {{research_context}} into the pipeline.
Edit it to match your research topic before running any step.
The research question goes in prompts/research_question.md.
This file holds everything domain-specific beyond the question itself.

---

## Submission Venue

# Name of the conference or journal you are submitting to,
# and what kind of venue it is (peer-reviewed, AI-focused, etc.).
# Example: "NeurIPS 2026 — a top-tier ML conference."




---

## Literature Review — Domains to Cover

# List the specific fields and sub-fields the literature
# review should cover for your topic. Be specific — vague domains
# produce vague reviews. Aim for 4-8 items.
# Example for a bias detection paper:
#   1. Bias detection and fairness in NLP
#   2. Dataset construction and annotation bias
#   3. Evaluation metrics for fairness
#   ...



## Literature Review — Theoretical Frameworks

# List the key theoretical papers, frameworks, or arguments
# that are central to your topic. These anchor the literature review
# and the Discussion section. Keep 3-5 items.
# Example: "Manning (2022) on emergent abilities — what they claim
#            vs what the evidence supports"



---

## Experiment Design — Constraints

# State what is and isn't in scope for the experiments.
# Cover: what tools/models you have access to, what you will NOT
# build from scratch, language/platform constraints, budget limits.
# Example: "We ARE using the HuggingFace API. We are NOT fine-tuning
#            any models. All code must run on a single GPU."



## Experiment Design — Evaluation

# Describe how outputs will be evaluated in your domain.
# Specify: automated vs human, what rubric, what scoring criteria,
# whether a judge model is used and how it should behave.
# If there is no domain-specific evaluation challenge, keep it brief:
# "All evaluation is automated using standard NLP metrics."



## Experiment Design — Domain Tools

# List every existing library, API, dataset, or tool
# relevant to your domain. The experiment design step will use
# this to choose what to integrate. Be specific: name, purpose,
# where to find it, known limitations.
# Example: "spaCy (NLP pipeline, pip install spacy, no support for
#            low-resource languages)"
# If you don't know what tools exist, write "unknown — let the
# pipeline discover them during the literature review."



---

## Code Generation Notes

# Any domain-specific instructions for how the experiment
# code should be written — constraints on prompts, things the model
# must NOT be told, specific output formats required, etc.
# Delete this section if you have no special code generation needs.


---

## Paper Writing Notes

# Domain-specific guidance for each paper section.
# These notes are injected into the paper-writing steps.
# Cover any framing, structure, or emphasis decisions that are
# specific to your topic and wouldn't be obvious from the RQs alone.
# Delete any sub-item that has no special requirement.


---

## Paper Review Notes

# Domain-specific issues to flag during the final review
# (Step 5e). These are things the generic review pass won't know
# to look for — unresolved threads, pending evaluations, claims
# that need grounding in your specific results.


