# PHASE 6c — Prompt Calibration Patch (Criteria 4 & 5)

## Context for Builder

This is Phase 6c — a targeted calibration patch based on test harness results. Phase 6b is complete and working. The system produces correct overall verdicts (NON_COMPLIANT, WORTH_CHECKING) but over-scores on two specific criteria.

**Problem identified:** Grok gives PASS to Criteria 4 (Empirical Test Path) and 5 (Falsifiability) when they should score CONDITIONAL_FAIL and FAIL respectively. Root cause analysis:

- **Criterion 4:** Grok credits a *described* methodology as an *operationalised* test. Having a methodology section is not the same as having pre-registered criteria, quantitative thresholds, or blind prediction sets.
- **Criterion 5:** Grok appears to be reading the falsifiability conditions from the form field metadata rather than assessing what's in the PDF itself. The form field had well-written falsifiers; the PDF does not contain explicit binary falsifiers with measurable thresholds.

**This is a prompt-only change in server.py.** No other files change.

---

## 1. Modify the Grok User Prompt

In the user prompt template in `server.py`, find the criteria descriptions section and replace the entries for criteria 4 and 5 with the following expanded versions. Keep all other criteria descriptions exactly as they are.

### Replace Criterion 4 description:

**Current:**
```
4. EMPIRICAL TEST PATH — Is there an explicit, operationalised test the claim could be subjected to? Pre-registered criteria? Quantitative thresholds?
```

**Replace with:**
```
4. EMPIRICAL TEST PATH — Is there an explicit, operationalised test the claim could be subjected to? IMPORTANT: A described methodology is NOT the same as an operationalised test. To score PASS, the PDF must contain ALL of: (a) pre-registered or clearly pre-defined test criteria, (b) quantitative statistical thresholds or metrics, (c) a specified dataset or prediction target defined BEFORE analysis. A methodology section that describes steps but lacks quantitative thresholds and pre-registered criteria is CONDITIONAL_FAIL at best. Retrospective pattern matching without blind prediction is CONDITIONAL_FAIL. Only score PASS if the test path is fully operationalised with measurable success/failure criteria.
```

### Replace Criterion 5 description:

**Current:**
```
5. FALSIFIABILITY — Is there a clear, measurable condition that would defeat the claim if observed? An explicit binary falsifier with a threshold?
```

**Replace with:**
```
5. FALSIFIABILITY — Is there a clear, measurable condition IN THE PDF DOCUMENT that would defeat the claim if observed? CRITICAL: Assess falsifiability from the PDF text ONLY, not from the form-field metadata above. The form fields are for orientation only. To score PASS, the PDF itself must contain an explicit binary falsifier with a specific measurable threshold (e.g., "if X exceeds Y, the claim is rejected"). Qualitative falsifiers ("if someone disproves it") or conditions that the framework could absorb through reinterpretation are FAIL. If the PDF describes conditions for falsification but without specific quantitative thresholds, score CONDITIONAL_FAIL. Only score PASS if the PDF contains at least one falsifier that is binary, measurable, and threshold-defined.
```

---

## 2. Add a General Instruction to the Prompt

Find the line in the user prompt that says:

```
SUBMISSION METADATA (provided for orientation only — assess from PDF text below, not from these fields):
```

Add the following line immediately after it:

```
CRITICAL INSTRUCTION: The metadata fields above (especially the falsifiability condition) are the submitter's SELF-DESCRIPTION of their work. They may be more polished than what the PDF actually contains. Always assess from the PDF text. If the PDF does not contain what the form field claims, score based on what is in the PDF, not what the form field says.
```

---

## 3. What NOT To Change

- Do NOT change any other criteria descriptions (1, 2, 3, 6, 7, 8, 9)
- Do NOT change the system message
- Do NOT change the response format or parsing
- Do NOT change the GitHub issue format
- Do NOT change the labelling logic
- Do NOT change any frontend code
- Do NOT change PDF extraction

---

## 4. Verification — Re-run the Cross-Domain Test

After applying the prompt changes, re-submit the Cross-Domain 72-12-4-7 PDF through the portal using the same form fields as issue #26.

### Expected improvement:

| # | Criterion | Issue #26 (before) | Target (after) | Geoff's verdict |
|---|---|---|---|---|
| 4 | Empirical Test Path | ✅ Pass | ⚠️ Conditional Fail | CONDITIONAL_FAIL |
| 5 | Falsifiability | ✅ Pass | ❌ Fail | FAIL |

All other criteria should remain the same or within one step of their issue #26 values.

### Acceptance criteria:

1. Criterion 4 scores CONDITIONAL_FAIL or CONDITIONAL_PASS (not PASS)
2. Criterion 5 scores FAIL or CONDITIONAL_FAIL (not PASS or CONDITIONAL_PASS)
3. Overall verdicts remain: NON_COMPLIANT + WORTH_CHECKING
4. No other criteria move by more than one step from their issue #26 values
5. Summary text remains balanced and structural (not hostile, not cheerleading)

If criterion 5 still scores PASS after this change, the form-field bleed is deeper than expected and we may need to remove the falsifiability form field from the metadata section entirely (send only title, claim, and scale to Grok, not the falsifiability text).

---

*Phase 6c of 6c — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
