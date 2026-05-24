RESEARCH QUESTION:
{{research_question}}

You are reviewing external feedback on the paper and deciding how to act on it.
You have full editorial authority — not all feedback must be applied.

COMPLETE PAPER (all sections):
{{05a_paper}}
{{05b_paper}}
{{05c_paper}}
{{05d_paper}}

EXTERNAL FEEDBACK:
{{feedback}}

YOUR TASK:
Read every comment in the feedback carefully. For each comment, decide:

1. APPLY — the comment is valid, relevant, and improves the paper
2. REJECT — the comment is invalid, already addressed, or would harm 
   the paper's coherence or argument
3. UPSTREAM — the comment requires changes to research questions, 
   hypotheses, or experimental setup — not the paper text itself

Do not apply a comment just because it exists.
Do not reject a comment just because it is critical.
Use your judgment as the paper's author.

---

OUTPUT FILE 1 — Paper Modifications (modifications section):

For each APPLIED comment, output exactly this format:

MODIFICATION N:
Feedback comment: "[exact quote from the feedback]"
Why relevant: [one sentence — why this comment is valid and improves the paper]
Section: [section name]
Location: [specific paragraph, table, or sentence]
Current: "[exact current text]"
Replace with: "[exact replacement text]"

---

For each REJECTED comment, output exactly this format:

REJECTED COMMENT N:
Feedback comment: "[exact quote from the feedback]"
Why rejected: [one sentence — why this comment does not apply or would harm the paper]

---

OUTPUT FILE 2 — Upstream Suggestions (upstream section):

For each UPSTREAM comment, output exactly this format:

UPSTREAM SUGGESTION N:
Feedback comment: "[exact quote from the feedback]"
Why upstream: [one sentence — why this requires changes beyond the paper text]
Suggested action: [specific change needed — which step, which file, what to modify]

---

IMPORTANT:
- Quote feedback comments exactly — do not paraphrase them
- Every comment in the feedback must appear in exactly one of the 
  three categories above — applied, rejected, or upstream
- Modifications must follow the same diff format as step 5e — 
  exact current text and exact replacement text only
- Do not rewrite whole sections — targeted changes only
- Writing style must remain natural and human — see system instructions