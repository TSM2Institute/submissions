# PHASE 1 — Language Fixes, Back Button & Criteria Reference

## Context for Builder

This is Phase 1 of a multi-phase update to the TSM2 Institute Submission Portal. This phase covers:

1. Language/wording updates throughout `index.html` and documentation
2. A "Return to Website" back button
3. A new Criteria Reference section (accordion-style) on the portal landing page

**No form restructuring in this phase.** The 5-step form stays exactly as-is. We're only changing wording, adding navigation, and adding an informational criteria section.

---

## 1. Language Updates (index.html)

### 1A. "Binary Compliance" → "Binary Structural Compliance"

Find every instance of "Binary Compliance Model" in `index.html` and replace with:

**"Binary Structural Compliance Model"**

Wherever this phrase appears, add the following disclaimer text nearby (as a subtitle, helper text, or note — whatever fits the existing design):

> Structural compliance does not constitute scientific validation or endorsement.

### 1B. AI Pre-Check Language

Find the section/text that describes the AI pre-check. Add this line:

> The AI pre-check evaluates structure, not scientific truth.

### 1C. Declaration Checkboxes

The current declaration section has these confirmations:
- Submitter has read and accepted the Submission Instructions
- Understands compliance is binary and does not imply endorsement
- Confirms the attached PDF is the authoritative version

**Update the second checkbox text to read:**

> Understands that structural compliance does not mean "Scientifically Proven" — it confirms the submission meets intake criteria only.

### 1D. Examiner Language

If there is any examiner-facing text in `index.html` (unlikely in the public form, but check), ensure it says:

> Examiner decision confirms structural compliance only. It does not certify scientific correctness.

---

## 2. Back Button / Return to Website

Add a visible "← Return to TSM2 Institute" link/button at the top of the page (header area). It should:

- Link to the main TSM2 Institute website (use `https://tsm2institute.org` as placeholder — Graham will confirm the correct URL)
- Be styled consistently with the existing design (cosmic/space theme, Inter font)
- Be subtle but clearly visible — not competing with the main form UI
- Position: top-left of the page, above the main content

---

## 3. Criteria Reference Section (Accordion)

Add a new section to the portal landing page **above the submission form** (or as a clearly labelled expandable section). This is informational — it tells submitters what their PDF needs to address.

### Section Title:
**"Submission Criteria — What Your PDF Must Address"**

### Subtitle:
> All submissions are evaluated against these 9 structural criteria. Your PDF document must address each one. Criterion 10 is assessed by the Examiner only.

### Accordion Items:

Build this using **Alpine.js** (already in the project) and **Tailwind CSS** (already in the project). Do NOT use Geoff's raw CSS/JS accordion code — rebuild it in the existing stack for consistency.

Each accordion item should be collapsible (click to expand/collapse). All collapsed by default.

Here are the 10 items:

---

**1. Explicit Claim**
The submission must clearly state what it is claiming. No ambiguity. No implication. No inference. The claim must be singular and non-compound.

**2. Definitions of Key Terms**
All key terms must be clearly defined and used consistently. Undefined or framework-specific terminology results in non-compliance.

**3. Declared Assumptions**
All foundational assumptions must be explicitly declared. Hidden premises invalidate compliance. Assumptions must be stated, not implied.

**4. Stated Mechanism (Causal Chain)**
The submission must describe the physical mechanism connecting cause to effect. Provide a step-by-step causal sequence. Assertion without mechanism is non-compliant.

**5. Energy / Conservation Consistency**
Energy must be conserved, tracked, and accounted for. Demonstrate how the claim preserves conservation laws, or clearly state which law is modified and why. No undefined energy sources or sinks permitted.

**6. Observational or Empirical Anchor**
The submission must identify the dataset, measurable phenomenon, or observational reference that grounds the claim. State how the claim interacts with real-world data.

**7. Falsifiability Condition**
There must be at least one identifiable condition under which the claim could be proven wrong. If it cannot fail, it cannot pass.

**8. Scale Consistency**
The model must operate consistently at the declared physical scale. No cross-scale substitution without explicit justification.

**9. Category Integrity**
The claim must not replace physical causation with metaphor, geometry, or undefined abstraction. Physical claims must have physical mechanisms.

**10. Why Is This Claim True? — *Examiner Assessment Only***
*(Style this item differently — greyed out or with a distinct visual indicator that it's examiner-only)*

The Examiner evaluates whether the submission answers in structured causal form: **"Because X interacts with Y, therefore Z."** This criterion is assessed by the qualified examiner, not by the submitter or the AI pre-check.

---

### Design Notes for the Accordion:

- Match the existing cosmic/space theme
- Dark background for accordion headers (consistent with existing UI)
- Light/readable expanded panels
- Use Inter font (already loaded)
- Criterion 10 should be visually distinct (e.g., border styling, opacity, or a badge saying "Examiner Only")
- Consider a small icon or indicator showing expand/collapse state (chevron or +/-)

---

## 4. Documentation Updates

### 4A. README.md

Update the following:
- "Binary Compliance Model" → "Binary Structural Compliance Model" everywhere
- Add to the AI Pre-Check section: "The AI pre-check evaluates structure, not scientific truth."
- Add a note under Examiner Workflow: "The Examiner decision applies only to structural compliance under Institute criteria and does not certify scientific correctness."

### 4B. replit.md

Same language updates as README.md:
- "Binary Compliance Model" → "Binary Structural Compliance Model"
- Note about AI evaluating structure not truth
- Examiner language clarification

---

## What NOT To Change in Phase 1

- Do NOT modify the form fields or form structure
- Do NOT change the API endpoint or server.py
- Do NOT modify the Grok AI prompt
- Do NOT change the GitHub issue markdown template
- Do NOT add or remove form steps

Phase 2 will handle form expansion and AI prompt updates.

---

## Verification Checklist (for Graham)

After applying these changes, confirm:

- [ ] "Binary Structural Compliance Model" appears everywhere "Binary Compliance" used to
- [ ] Disclaimer text visible: "Structural compliance does not constitute scientific validation"
- [ ] AI pre-check note visible: "evaluates structure, not scientific truth"
- [ ] Declaration checkbox wording updated
- [ ] Back button present and links correctly
- [ ] Criteria accordion renders with all 10 items
- [ ] Criterion 10 is visually distinct (examiner-only)
- [ ] All accordions expand/collapse correctly
- [ ] No form functionality broken — test a submission end-to-end
- [ ] README.md language updated
- [ ] replit.md language updated

---

*Phase 1 of 5 — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
