RESEARCH QUESTION:
{{research_question}}


CRITICAL — DOUBLE-BLIND POLICY:
Double-blind means author names and affiliations are omitted.
It does NOT mean hiding experimental details.
Always state explicitly: model names, versions, API parameters,
tools used, evaluation metrics. A reviewer must be able to
reproduce every experiment from what is written.

Review the complete paper below and identify required modifications.

COMPLETE PAPER SECTIONS:
{{05a_paper}}
{{05b_paper}}
{{05c_paper}}
{{05d_paper}}

YOUR TASK:
Do NOT rewrite any section.
Do NOT reproduce any existing content.
Do NOT generate the full paper again.

Output ONLY a list of specific, targeted modifications in exactly 
this format:

---
MODIFICATION N:
Section: [section name]
Location: [paragraph number, table, or specific sentence]
Current: "[exact current text — quote it precisely]"
Replace with: "[exact replacement text]"
Reason: [one sentence explaining why this change is needed]
---

WHAT TO LOOK FOR:
1. Arguments repeated across sections — flag and resolve
2. Claims in Discussion not supported by Results — flag
3. Abstract claims that don't match what was actually written — fix
4. Citations used inconsistently — fix
5. Contradictions between sections — resolve
6. Gaps in the argument — where is the logical chain broken?
7. Model name, version, temperature, max tokens stated explicitly 
   everywhere they are referenced — replace any vague term like 
   'a frontier LLM' or 'the model' with the actual model name 
   and version from the experimental results
8. Any section that exceeds its purpose — e.g. interpretation 
   sneaking into Results, or new claims appearing in Conclusion
9. Mechanical or unnatural writing — flag sentences that:
   - Start with "It is worth noting", "It should be mentioned", "As such"
   - Use passive voice where active would be clearer
   - Repeat the same sentence structure three times in a row
   - Summarise what the previous paragraph just said
   Replace with natural, direct prose.

10. Domain-specific review notes from research context:
{{research_context}}

11. Title — does the recommended title accurately reflect the paper 
    as finally written? If the argument shifted during writing, 
    the title may need updating. Flag if so.

Only output modifications that are genuinely necessary.
If a section is correct, say nothing about it.