# Research Context

This file is injected as {{research_context}} into the pipeline.
Edit it to match your research topic before running any step.
The research question goes in prompts/research_question.md.
This file holds everything domain-specific beyond the question itself.

---

## Submission Venue

# REPLACE: Name of the conference or journal you are submitting to,
# and what kind of venue it is (peer-reviewed, AI-focused, etc.).
# Example: "NeurIPS 2026 — a top-tier ML conference."

CAISc 2026 — a conference where AI systems are recognized as primary
contributors to scientific research.
Submit at: https://openreview.net/group?id=CAISc/2026

---

## Literature Review — Domains to Cover

# REPLACE: List the specific fields and sub-fields the literature
# review should cover for your topic. Be specific — vague domains
# produce vague reviews. Aim for 4-8 items.
# Example for a bias detection paper:
#   1. Bias detection and fairness in NLP
#   2. Dataset construction and annotation bias
#   3. Evaluation metrics for fairness
#   ...

1. AI and poetry generation across languages — note which languages
   have been studied, which haven't, and what that distribution reveals
2. NLP for Sanskrit, Telugu, Kannada specifically
3. Computational prosody and metrical analysis tools
4. Philosophy of language understanding in AI systems
5. Cross-linguistic evaluation methodology
6. Classical Indic poetics — rasa theory, dhvani, chandas literature

## Literature Review — Theoretical Frameworks

# REPLACE: List the key theoretical papers, frameworks, or arguments
# that are central to your topic. These anchor the literature review
# and the Discussion section. Keep 3-5 items.
# Example: "Manning (2022) on emergent abilities — what they claim
#            vs what the evidence supports"

After completing the review, identify the 3 most relevant theoretical
frameworks. Consider but do not limit yourself to:
- Bender & Koller (2020) "Climbing towards NLU" — form vs meaning
- Searle's Chinese Room argument — syntax vs semantics
- Chomsky's competence vs performance distinction
- Standard LLM evaluation metrics (BLEU, BERTScore, perplexity)
  and why they are insufficient for poetry

---

## Experiment Design — Constraints

# REPLACE: State what is and isn't in scope for the experiments.
# Cover: what tools/models you have access to, what you will NOT
# build from scratch, language/platform constraints, budget limits.
# Example: "We ARE using the HuggingFace API. We are NOT fine-tuning
#            any models. All code must run on a single GPU."

- We are NOT building prosody validators from scratch
- We are NOT training any models
- We ARE calling existing LLMs via API: Claude (Anthropic),
  GPT-4o (OpenAI), Gemini (Google), DeepSeek
- We ARE using whatever existing prosody tools exist for Sanskrit,
  Telugu, and Kannada
- All code must be runnable in Python

## Experiment Design — Evaluation

# REPLACE: Describe how outputs will be evaluated in your domain.
# Specify: automated vs human, what rubric, what scoring criteria,
# whether a judge model is used and how it should behave.
# If there is no domain-specific evaluation challenge, keep it brief:
# "All evaluation is automated using standard NLP metrics."

All evaluation must be fully automated. No human judges.

Where aesthetic or cultural judgment is required — rasa evaluation,
dhvani assessment, metrical appropriateness, aucitya — use a
separate LLM instance acting as a simulated sahrdaya:
- A different model from the generator wherever possible
  (e.g. if Claude generates, GPT-4o evaluates — and vice versa)
- Given explicit classical poetics criteria in its system prompt:
  rasa categories, dhvani definition, aucitya, metrical mood-affiliations
- Required to justify every judgment with reasoning — a bare score
  without reasoning is invalid
- Asked to rate on a structured rubric, not a holistic impression

For RQ3 — iterative refinement loop:
- Generator LLM produces a verse
- Simulated sahrdaya LLM evaluates against rasa/dhvani criteria
  and provides structured feedback
- Generator receives feedback and produces a revised verse
- Repeat for 3-5 cycles, logging every generation, evaluation, revision
- The question is whether the loop converges toward aesthetic quality
  and what the trajectory reveals about the locus of poetic understanding

## Experiment Design — Domain Tools

# REPLACE: List every existing library, API, dataset, or tool
# relevant to your domain. The experiment design step will use
# this to choose what to integrate. Be specific: name, purpose,
# where to find it, known limitations.
# Example: "spaCy (NLP pipeline, pip install spacy, no support for
#            low-resource languages)"
# If you don't know what tools exist, write "unknown — let the
# pipeline discover them during the literature review."

List every existing Python library, API, or tool available for:
- Sanskrit prosody analysis
- Telugu prosody analysis
- Kannada prosody analysis
- General Indic NLP
Include: library name, what it does, where to find it, known limitations.

---

## Code Generation Notes

# REPLACE: Any domain-specific instructions for how the experiment
# code should be written — constraints on prompts, things the model
# must NOT be told, specific output formats required, etc.
# Delete this section if you have no special code generation needs.

For Experiment 2 specifically: do NOT include the guru/laghu rules
in the prompt — the model must demonstrate what it knows without
being coached. The prompt should simply ask the model to assign G/L
based on its own knowledge of the language's prosody.

---

## Paper Writing Notes

# REPLACE: Domain-specific guidance for each paper section.
# These notes are injected into the paper-writing steps.
# Cover any framing, structure, or emphasis decisions that are
# specific to your topic and wouldn't be obvious from the RQs alone.
# Delete any sub-item that has no special requirement.

Introduction: Motivate metrical poetry in Sanskrit, Telugu, and
Kannada as the diagnostic instrument for LLM language understanding.

Methodology: Document the sahṛdaya panel setup for Experiment 3,
including selection criteria and evaluation protocol.

Results: Include a cross-linguistic comparison — does the failure
pattern differ across Sanskrit, Telugu, and Kannada, and what does
that reveal about what LLMs have and haven't learned?

Discussion: Connect findings to Bender & Koller (2020), Searle's
Chinese Room, and Chomsky's competence vs performance — but only
where genuinely supported by the results.

---

## Paper Review Notes

# REPLACE: Domain-specific issues to flag during the final review
# (Step 5e). These are things the generic review pass won't know
# to look for — unresolved threads, pending evaluations, claims
# that need grounding in your specific results.
# Delete this section if you have no special review requirements.

- Rasa evaluation described as pending — resolve: either report
  results or explicitly reframe as future work in methodology
