# PHASE 3 — AI Prompt Upgrade: 9-Criteria Scorecard

## Context for Builder

This is Phase 3 of the TSM2 Submission Portal update. Phases 1 and 2 are complete and verified.

Phase 3 upgrades the Grok AI pre-check from 4 loose checks to a structured 9-criteria scorecard. This changes:
- The Grok prompt in `server.py`
- The response parsing in `server.py`
- The AI results section in the GitHub issue markdown

**The AI pre-check remains non-authoritative.** Submissions proceed regardless of result. The upgrade gives examiners a more useful structural assessment — not a gate.

---

## 1. Updated Grok Prompt (server.py)

Replace the current Grok prompt construction with the following. Keep the same API call structure (endpoint, model, temperature, etc.) — only the prompt content and response parsing change.

### System Message (replace existing):

```
You are a structural compliance screener for the TSM2 Institute for Cosmology. You evaluate whether submissions meet 9 defined structural criteria. You assess structure and completeness, not scientific truth. Respond only with valid JSON.
```

### User Prompt (replace existing):

```
You are screening a submission to the TSM2 Institute for Cosmology against 9 structural criteria. Evaluate structure and completeness only — do NOT judge scientific merit or correctness.

SUBMISSION DATA:
- Title: {submission_title}
- Core Claim: {core_claim}
- Primary Scale: {primary_scale}
- Falsifiability Condition: {falsifiability}

SUBMITTER SELF-CERTIFICATION:
The submitter has confirmed their PDF addresses the following (these are declarations, not content you can verify — note them as "Declared by submitter"):
- Key terms defined: {criteria_definitions}
- Assumptions declared: {criteria_assumptions}
- Mechanism described: {criteria_mechanism}
- Energy conservation addressed: {criteria_energy}
- Empirical anchor identified: {criteria_empirical}
- Category integrity maintained: {criteria_category}

EVALUATE AGAINST THESE 9 CRITERIA:

1. EXPLICIT CLAIM — Is the core claim singular, clear, and non-compound? (Assess from the Core Claim field)
2. KEY TERM DEFINITIONS — Has the submitter declared their PDF defines key terms? (Check self-certification)
3. DECLARED ASSUMPTIONS — Has the submitter declared their PDF states assumptions? (Check self-certification)
4. STATED MECHANISM — Has the submitter declared their PDF describes a causal mechanism? (Check self-certification)
5. ENERGY CONSERVATION — Has the submitter declared their PDF addresses conservation laws? (Check self-certification)
6. EMPIRICAL ANCHOR — Has the submitter declared their PDF identifies observational grounding? (Check self-certification)
7. FALSIFIABILITY — Is the falsifiability condition testable and specific? (Assess from the Falsifiability field)
8. SCALE CONSISTENCY — Is a physical or cosmological scale stated? Does the claim appear consistent with that scale? (Assess from Primary Scale and Core Claim fields)
9. CATEGORY INTEGRITY — Does the core claim use physical causation rather than metaphor or undefined abstraction? (Assess from the Core Claim field)

For criteria 2-6: If the submitter has self-certified (true), mark as "DECLARED" with a note. If false, mark as "MISSING".
For criteria 1, 7, 8, 9: Assess the actual content provided in the form fields.

Respond in this exact JSON format only — no markdown, no preamble:
{
  "criteria": [
    {"id": 1, "name": "Explicit Claim", "status": "PASS|FLAG|MISSING", "note": "Brief explanation"},
    {"id": 2, "name": "Key Term Definitions", "status": "DECLARED|MISSING", "note": "Brief explanation"},
    {"id": 3, "name": "Declared Assumptions", "status": "DECLARED|MISSING", "note": "Brief explanation"},
    {"id": 4, "name": "Stated Mechanism", "status": "DECLARED|MISSING", "note": "Brief explanation"},
    {"id": 5, "name": "Energy Conservation", "status": "DECLARED|MISSING", "note": "Brief explanation"},
    {"id": 6, "name": "Empirical Anchor", "status": "DECLARED|MISSING", "note": "Brief explanation"},
    {"id": 7, "name": "Falsifiability", "status": "PASS|FLAG", "note": "Brief explanation"},
    {"id": 8, "name": "Scale Consistency", "status": "PASS|FLAG", "note": "Brief explanation"},
    {"id": 9, "name": "Category Integrity", "status": "PASS|FLAG", "note": "Brief explanation"}
  ],
  "overall": "PASSED|NEEDS REVIEW",
  "summary": "One sentence overall assessment"
}

Status values:
- PASS = criterion clearly met based on assessed content
- DECLARED = submitter self-certified their PDF addresses this (cannot be verified from form data alone)
- FLAG = potential issue identified — examiner should check
- MISSING = not addressed or not certified

Overall result:
- PASSED = all criteria are PASS or DECLARED, no FLAGS or MISSING
- NEEDS REVIEW = one or more criteria are FLAG or MISSING
```

### Template Variables:

The `{submission_title}`, `{core_claim}`, `{primary_scale}`, and `{falsifiability}` variables should continue to be pulled from `formData` exactly as they are now.

The new self-certification variables should be pulled from `formData` as well:
- `{criteria_definitions}` → `formData.criteria_definitions` (boolean: true/false)
- `{criteria_assumptions}` → `formData.criteria_assumptions` (boolean: true/false)
- `{criteria_mechanism}` → `formData.criteria_mechanism` (boolean: true/false)
- `{criteria_energy}` → `formData.criteria_energy` (boolean: true/false)
- `{criteria_empirical}` → `formData.criteria_empirical` (boolean: true/false)
- `{criteria_category}` → `formData.criteria_category` (boolean: true/false)

### Model & Parameters (unchanged):

- Model: `grok-3-mini`
- Temperature: `0.3`
- Endpoint: `https://api.x.ai/v1/chat/completions`

---

## 2. Response Parsing (server.py)

The current code expects: `{"compliant": true/false, "message": "..."}`

Update the parsing to handle the new format: `{"criteria": [...], "overall": "...", "summary": "..."}`

### Parsing Logic:

```python
# Parse the new scorecard format
try:
    ai_result = json.loads(response_text)
    criteria = ai_result.get("criteria", [])
    overall = ai_result.get("overall", "NEEDS REVIEW")
    summary = ai_result.get("summary", "No summary provided.")
    
    # Determine the boolean compliant flag for backward compatibility
    compliant = (overall == "PASSED")
    
except (json.JSONDecodeError, KeyError):
    # Fallback if AI returns unexpected format
    criteria = []
    overall = "NEEDS REVIEW"
    summary = "AI pre-check returned an unexpected format. Manual review required."
    compliant = False
```

### Backward Compatibility:

The server response to the frontend should still include the `compliant` boolean and a `message` field for the success/confirmation screen. Add the scorecard data alongside:

```python
response_data = {
    "success": True,
    "html_url": issue_url,
    "number": issue_number,
    "complianceCheck": {
        "compliant": compliant,
        "message": summary,
        "overall": overall,
        "criteria": criteria  # Full scorecard
    }
}
```

The frontend success screen can continue to show the simple PASSED/NEEDS REVIEW message. The detailed scorecard goes in the GitHub issue (see section 3).

---

## 3. GitHub Issue Markdown — Updated AI Section

Replace the current AI Compliance Pre-Check section in the issue body with a detailed scorecard.

### New format (appended to issue by server after PDF link is resolved):

```markdown
---

### AI Structural Pre-Check (9-Criteria Scorecard)

> **This is an automated structural screening, not a scientific evaluation.**
> The AI pre-check evaluates structure, not scientific truth.
> Final compliance determination is made by a qualified examiner.

**Overall: {overall}**

| # | Criterion | Status | Note |
|---|-----------|--------|------|
| 1 | Explicit Claim | {status} | {note} |
| 2 | Key Term Definitions | {status} | {note} |
| 3 | Declared Assumptions | {status} | {note} |
| 4 | Stated Mechanism | {status} | {note} |
| 5 | Energy Conservation | {status} | {note} |
| 6 | Empirical Anchor | {status} | {note} |
| 7 | Falsifiability | {status} | {note} |
| 8 | Scale Consistency | {status} | {note} |
| 9 | Category Integrity | {status} | {note} |

**Summary:** {summary}
```

### Building the Markdown:

In server.py, after parsing the AI response, build the scorecard markdown from the `criteria` list:

```python
scorecard_rows = ""
for c in criteria:
    scorecard_rows += f"| {c['id']} | {c['name']} | {c['status']} | {c['note']} |\n"
```

Then insert `scorecard_rows` into the markdown template above.

### Fallback:

If the AI pre-check fails (API error, bad response, missing key), fall back to:

```markdown
---

### AI Structural Pre-Check (9-Criteria Scorecard)

> **This is an automated structural screening, not a scientific evaluation.**

**Overall: UNAVAILABLE**

AI pre-check could not be completed. This does not affect the submission — it will proceed to manual review.

**Reason:** {error_description}
```

---

## 4. What NOT To Change in Phase 3

- Do NOT modify the form fields or form structure (Phase 2 is locked)
- Do NOT modify index.html (unless the frontend success message needs minor adjustment)
- Do NOT add GitHub labels yet (Phase 4)
- Do NOT change the PDF upload, validation, or storage
- Do NOT change the email notification
- Do NOT change the API endpoint path or method

---

## 5. Edge Cases to Handle

### 5A. Self-certification fields missing from older submissions
If `formData` doesn't contain the new criteria boolean fields (e.g., from a cached form), default them to `false` in the server:

```python
criteria_definitions = form_data.get("criteria_definitions", False)
criteria_assumptions = form_data.get("criteria_assumptions", False)
# ... etc
```

### 5B. Grok API timeout or error
The current behavior (submission proceeds without AI data) should be preserved. Just update the fallback message to reference the new format.

### 5C. Grok returns old format
If Grok returns the old `{"compliant": true, "message": "..."}` format instead of the new scorecard (unlikely but possible), detect it and convert:

```python
if "criteria" not in ai_result and "compliant" in ai_result:
    # Old format fallback
    overall = "PASSED" if ai_result["compliant"] else "NEEDS REVIEW"
    summary = ai_result.get("message", "Legacy format response.")
    criteria = []  # No detailed breakdown available
```

---

## Verification Checklist (for Graham)

After applying these changes, confirm:

- [ ] Make a test submission with all criteria checkboxes checked
- [ ] GitHub issue contains the new 9-criteria scorecard table
- [ ] Scorecard shows proper statuses (PASS/DECLARED/FLAG)
- [ ] Overall result shows PASSED or NEEDS REVIEW
- [ ] Summary line is present and readable
- [ ] Disclaimer text appears above the scorecard
- [ ] Frontend success screen still works (shows PASSED/NEEDS REVIEW)
- [ ] Test with a deliberately vague claim — confirm AI flags it appropriately
- [ ] Test with a clearly structured claim — confirm PASSED result
- [ ] If possible, test API error handling (e.g., temporarily use wrong API key) — confirm fallback message appears in issue
- [ ] PDF upload still works
- [ ] Email notification still sends
- [ ] Previous test issues (like #13) are unaffected

---

*Phase 3 of 5 — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
