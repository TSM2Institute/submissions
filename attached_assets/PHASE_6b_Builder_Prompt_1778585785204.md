# PHASE 6b — PDF-Grounded AI Assessment

## Context for Builder

This is Phase 6b of the TSM2 Submission Portal update. Phase 6a (criteria realignment on frontend + docs) is complete.

Phase 6b is the core upgrade: the AI pre-check now reads the actual PDF content instead of only evaluating form fields. This is the most significant server-side change in the project. It involves:

1. Adding PDF text extraction (pdfplumber)
2. Replacing the Grok prompt entirely
3. Replacing the response parsing for the new 4-state scale and dual verdicts
4. Updating the GitHub issue scorecard format
5. Updating the auto-labelling logic

**The pre-check remains non-authoritative.** Submissions proceed regardless of AI verdict. The upgrade answers Geoffrey Thwaites' threshold question: "Is this a good enough submission for someone to check?"

---

## 1. Install pdfplumber

```bash
pip install pdfplumber
```

Import at the top of `server.py`:

```python
import pdfplumber
```

`pdfplumber` is preferred over `pypdf` for scientific PDFs — it handles columns, tables, and embedded text more reliably.

If `pdfplumber` cannot be installed for any reason, fall back to `pypdf2` or `PyPDF2` and note the limitation in a code comment.

---

## 2. PDF Text Extraction

### When to extract:

After the PDF is saved to `/uploads/` and validated, but BEFORE the Grok API call.

### Extraction function:

```python
def extract_pdf_text(pdf_path, max_chars=60000):
    """Extract text from PDF using pdfplumber.
    
    Returns (text, truncated, page_count) tuple.
    - text: extracted text content
    - truncated: boolean, True if text was cut short
    - page_count: total number of pages in the PDF
    """
    try:
        text_parts = []
        total_chars = 0
        truncated = False
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    if total_chars + len(page_text) > max_chars:
                        # Truncate at page boundary
                        remaining = max_chars - total_chars
                        text_parts.append(page_text[:remaining])
                        text_parts.append("\n\n[--- PDF TEXT TRUNCATED AT CHARACTER LIMIT ---]")
                        truncated = True
                        break
                    text_parts.append(page_text)
                    total_chars += len(page_text)
        
        return "\n\n".join(text_parts), truncated, page_count
        
    except Exception as e:
        print(f"[PDF EXTRACTION ERROR] {e}")
        return None, False, 0
```

### Integration point:

After saving the PDF file and before the Grok API call:

```python
# Extract PDF text for AI assessment
pdf_text, pdf_truncated, pdf_page_count = extract_pdf_text(saved_pdf_path)

if pdf_text is None:
    pdf_text = "[PDF text could not be extracted. The AI pre-check will proceed with form fields only.]"
    pdf_extraction_failed = True
else:
    pdf_extraction_failed = False
```

---

## 3. Replace the Grok Prompt

### System message (replace existing):

```
You are a structural compliance screener for the TSM2 Institute for Cosmology. Your task is to assess scientific submissions against 9 structural criteria covering claim clarity, mechanism, falsifiability, methodology, predictive capability, and reproducibility. You assess structure and methodological discipline, not scientific truth, and not agreement with any particular theoretical framework. A submission can be excellent structurally while contradicting TSM2, or be aligned with TSM2 while failing structurally. Judge structure only. Respond only with valid JSON in the schema specified.
```

### User prompt template (replace existing):

```
You are screening a submission to the TSM2 Institute for Cosmology against 9 structural criteria. Evaluate structure, methodology, and epistemic discipline only — do NOT judge scientific merit, correctness, or alignment with any framework.

SUBMISSION METADATA (provided for orientation only — assess from PDF text below, not from these fields):
- Title: {submission_title}
- Submitter's stated core claim: {core_claim}
- Submitter's stated primary scale: {primary_scale}
- Submitter's stated falsifiability condition: {falsifiability}

PDF TEXT:
---
{pdf_text}
---

EVALUATE AGAINST THESE 9 CRITERIA, using the four-state scale (PASS, CONDITIONAL_PASS, CONDITIONAL_FAIL, FAIL):

1. CLEAR SINGULAR CLAIM — Is there a single, identifiable, operationally testable claim?
2. DEFINED TERMS AND ONTOLOGY — Are key terms operationally defined? Is the mathematical layer separated from the empirical layer where applicable?
3. CAUSAL MECHANISM — Is a physical or structural mechanism proposed that explains why the claim holds? Note: if the paper explicitly disclaims causality, mark FAIL.
4. EMPIRICAL TEST PATH — Is there an explicit, operationalised test the claim could be subjected to? Pre-registered criteria? Quantitative thresholds?
5. FALSIFIABILITY — Is there a clear, measurable condition that would defeat the claim if observed? An explicit binary falsifier with a threshold?
6. DEPENDENCY TRANSPARENCY — Does the author explicitly acknowledge assumptions, limitations, and interpretive judgements?
7. NON-ARBITRARY SELECTION — Is the analysis protected against confirmation bias and post-hoc selection? Was the target defined before the search, or selected from the search?
8. PREDICTIVE CAPABILITY — Does the claim generate novel testable predictions of undiscovered phenomena, or does it only re-describe existing data?
9. REPRODUCIBILITY — Could an independent reviewer follow the methodology to replicate the analysis?

For each criterion, return:
- status: one of PASS, CONDITIONAL_PASS, CONDITIONAL_FAIL, FAIL
- note: one or two sentences explaining the verdict, citing what is or is not present in the PDF

Then compute two overall verdicts:

COMPLIANCE_VERDICT:
- COMPLIANT if ALL 9 criteria are PASS
- NON_COMPLIANT otherwise

WORTH_CHECKING_VERDICT:
- WORTH_CHECKING if Criterion 1 is PASS or CONDITIONAL_PASS, AND at least 2 of (Criterion 2, Criterion 6, Criterion 9) are PASS or CONDITIONAL_PASS
- NOT_WORTH_CHECKING otherwise

Respond in this exact JSON format only — no markdown, no preamble, no trailing text:

{"criteria": [{"id": 1, "name": "Clear Singular Claim", "status": "...", "note": "..."},{"id": 2, "name": "Defined Terms and Ontology", "status": "...", "note": "..."},{"id": 3, "name": "Causal Mechanism", "status": "...", "note": "..."},{"id": 4, "name": "Empirical Test Path", "status": "...", "note": "..."},{"id": 5, "name": "Falsifiability", "status": "...", "note": "..."},{"id": 6, "name": "Dependency Transparency", "status": "...", "note": "..."},{"id": 7, "name": "Non-Arbitrary Selection", "status": "...", "note": "..."},{"id": 8, "name": "Predictive Capability", "status": "...", "note": "..."},{"id": 9, "name": "Reproducibility", "status": "...", "note": "..."}],"compliance_verdict": "COMPLIANT|NON_COMPLIANT","worth_checking_verdict": "WORTH_CHECKING|NOT_WORTH_CHECKING","summary": "One paragraph (3-5 sentences) summarising the submission's structural standing — what it does well, what it lacks, and what would need to change to reach compliance."}
```

### Template variable notes:

- `{submission_title}`, `{core_claim}`, `{primary_scale}`, `{falsifiability}` — from formData, same as before
- `{pdf_text}` — from the `extract_pdf_text()` function output

### Model and parameters:

- Model: `grok-3-mini` (unchanged)
- Temperature: `0.3` (unchanged)
- **max_tokens: increase to 2000** (the response is now longer with 9 detailed notes + summary paragraph)

### If PDF extraction failed:

Replace the `{pdf_text}` section with:

```
PDF TEXT:
---
[PDF text could not be extracted. Assess based on the metadata fields above only. Note in your summary that the assessment is limited to form fields due to PDF extraction failure.]
---
```

The assessment proceeds with reduced confidence. This is a graceful degradation, not a hard failure.

---

## 4. Response Parsing

### Replace the current parsing logic with:

```python
try:
    ai_result = json.loads(response_text)
    criteria = ai_result.get("criteria", [])
    compliance_verdict = ai_result.get("compliance_verdict", "NON_COMPLIANT")
    worth_checking_verdict = ai_result.get("worth_checking_verdict", "NOT_WORTH_CHECKING")
    summary = ai_result.get("summary", "No summary provided.")
    
    # Backward compatibility: derive simple boolean
    compliant = (compliance_verdict == "COMPLIANT")
    
except (json.JSONDecodeError, KeyError, TypeError):
    criteria = []
    compliance_verdict = "UNAVAILABLE"
    worth_checking_verdict = "UNAVAILABLE"
    summary = "AI pre-check returned an unexpected format. Manual review required."
    compliant = False
```

### Handle markdown-wrapped JSON:

Grok sometimes wraps JSON in markdown code fences. Strip them before parsing:

```python
# Strip markdown code fences if present
response_text = response_text.strip()
if response_text.startswith("```json"):
    response_text = response_text[7:]
if response_text.startswith("```"):
    response_text = response_text[3:]
if response_text.endswith("```"):
    response_text = response_text[:-3]
response_text = response_text.strip()
```

### Legacy format detection:

If Grok returns the old Phase 3 format (unlikely but handle it):

```python
if "criteria" not in ai_result and "compliant" in ai_result:
    compliance_verdict = "COMPLIANT" if ai_result["compliant"] else "NON_COMPLIANT"
    worth_checking_verdict = "WORTH_CHECKING"  # Assume worth checking on legacy
    summary = ai_result.get("message", "Legacy format response.")
    criteria = []
```

---

## 5. GitHub Issue Scorecard — New Format

Replace the current AI pre-check section in the GitHub issue with:

### When AI succeeds (criteria list populated):

```markdown
---

### AI Structural Pre-Check (9-Criteria Scorecard, PDF-grounded)

> **This is an automated structural screening, not a scientific evaluation.**
> The AI pre-check evaluates structure, not scientific truth.
> A submission that contradicts TSM2 can still pass; a submission that agrees with TSM2 can still fail.
> Final compliance determination is made by a qualified examiner.

**Compliance Verdict:** {compliance_verdict}
**Worth Checking Verdict:** {worth_checking_verdict}

| # | Criterion | Status | Note |
|---|-----------|--------|------|
| 1 | Clear Singular Claim | {rendered_status} | {note} |
| 2 | Defined Terms and Ontology | {rendered_status} | {note} |
| 3 | Causal Mechanism | {rendered_status} | {note} |
| 4 | Empirical Test Path | {rendered_status} | {note} |
| 5 | Falsifiability | {rendered_status} | {note} |
| 6 | Dependency Transparency | {rendered_status} | {note} |
| 7 | Non-Arbitrary Selection | {rendered_status} | {note} |
| 8 | Predictive Capability | {rendered_status} | {note} |
| 9 | Reproducibility | {rendered_status} | {note} |

**Summary:** {summary}
```

### Status rendering:

Render the status values with emoji for readability in GitHub:

```python
STATUS_DISPLAY = {
    "PASS": "✅ Pass",
    "CONDITIONAL_PASS": "⚠️ Conditional Pass",
    "CONDITIONAL_FAIL": "⚠️ Conditional Fail",
    "FAIL": "❌ Fail"
}
```

Use: `STATUS_DISPLAY.get(criterion["status"], criterion["status"])`

### When AI fails (empty criteria list):

```markdown
---

### AI Structural Pre-Check (9-Criteria Scorecard, PDF-grounded)

> **This is an automated structural screening, not a scientific evaluation.**

**Compliance Verdict:** UNAVAILABLE
**Worth Checking Verdict:** UNAVAILABLE

The AI pre-check could not be completed. This does not affect the submission — it proceeds to manual review.

**Reason:** {error_description}
```

### If PDF was truncated, add a note:

After the scorecard table, before the summary, add:

```markdown
> ⚠️ Note: The PDF text was truncated at approximately 60,000 characters ({pdf_page_count} pages total). The AI assessment is based on the content up to the truncation point.
```

### If PDF extraction failed, add a note:

```markdown
> ⚠️ Note: PDF text extraction failed. The AI assessment is based on form-field metadata only, with reduced confidence.
```

---

## 6. Auto-Labelling — Updated Logic

Replace the current label logic with:

```python
# Determine labels
labels = ["Pending Review"]  # Always applied

if compliance_verdict == "COMPLIANT":
    labels.append("AI Pre-Check: Compliant")
elif compliance_verdict == "NON_COMPLIANT" and worth_checking_verdict == "WORTH_CHECKING":
    labels.append("AI Pre-Check: Worth Checking")
elif worth_checking_verdict == "NOT_WORTH_CHECKING":
    labels.append("AI Pre-Check: Structural Issues")
elif compliance_verdict == "UNAVAILABLE":
    labels.append("Screening: Unavailable")
```

### New labels to create:

In addition to the existing labels, ensure these exist in the GitHub repo:

| Label | Color (hex) | Description |
|-------|-------------|-------------|
| `AI Pre-Check: Compliant` | `#0E8A16` (green) | All 9 criteria passed |
| `AI Pre-Check: Worth Checking` | `#1D76DB` (blue) | Non-compliant but demonstrates epistemic hygiene |
| `AI Pre-Check: Structural Issues` | `#D93F0B` (orange) | Does not meet basic structural threshold |
| `Screening: Unavailable` | `#D93F0B` (orange) | AI pre-check could not be completed (kept from Phase 4) |

The old labels (`Screening: Passed`, `Screening: Needs Review`) can be kept in the repo for historical issues but will no longer be auto-applied to new submissions.

---

## 7. Frontend Response Update

Update the API response to include the new fields:

```python
response_data = {
    "success": True,
    "html_url": issue_url,
    "number": issue_number,
    "complianceCheck": {
        "compliant": compliant,  # backward compat boolean
        "message": summary,
        "compliance_verdict": compliance_verdict,
        "worth_checking_verdict": worth_checking_verdict,
        "criteria": criteria
    }
}
```

The frontend success screen currently shows a simple PASSED/NEEDS REVIEW message. Update this to show the new verdicts:

### Frontend display logic (in index.html):

If `compliance_verdict == "COMPLIANT"`:
> ✅ **AI Structural Pre-Check: COMPLIANT** — All 9 criteria passed.

If `compliance_verdict == "NON_COMPLIANT"` and `worth_checking_verdict == "WORTH_CHECKING"`:
> ⚠️ **AI Structural Pre-Check: WORTH CHECKING** — Some criteria need attention, but the submission demonstrates sufficient structural discipline for examiner review.

If `worth_checking_verdict == "NOT_WORTH_CHECKING"`:
> ❌ **AI Structural Pre-Check: STRUCTURAL ISSUES** — The submission does not yet meet the structural threshold. Please review the scorecard on your GitHub issue and consider revising.

If verdicts are `"UNAVAILABLE"`:
> ℹ️ **AI Structural Pre-Check: UNAVAILABLE** — The automated check could not be completed. Your submission will proceed to manual review.

**In all cases:** Show the "View Issue on GitHub" link as before. The submission always proceeds.

---

## 8. Submitter Email Content Update

Update the email content templates (the ones currently logged server-side) to reflect the new verdicts:

### COMPLIANT email:
Same structure as before but replace "PASSED" with "COMPLIANT" and note all 9 criteria passed.

### WORTH CHECKING email:
Replace the old "NEEDS REVIEW" template. Show the dual verdicts:
```
AI STRUCTURAL PRE-CHECK:
- Compliance Verdict: NON-COMPLIANT
- Worth Checking Verdict: WORTH CHECKING

Your submission demonstrates structural discipline but has areas requiring attention.
The following criteria were not fully met:

{list only criteria with CONDITIONAL_FAIL or FAIL status}

Your submission will proceed to examiner review.
```

### STRUCTURAL ISSUES email:
New template for NOT_WORTH_CHECKING:
```
AI STRUCTURAL PRE-CHECK:
- Compliance Verdict: NON-COMPLIANT
- Worth Checking Verdict: NOT WORTH CHECKING

The automated screening identified significant structural gaps:

{list criteria with FAIL or CONDITIONAL_FAIL status}

Please review the full scorecard on your GitHub issue and consider revising your submission before resubmitting.
```

### UNAVAILABLE email:
Same as before — screening couldn't complete, submission proceeds to manual review.

---

## 9. Error Handling & Edge Cases

### 9A. PDF text is empty
Some PDFs are scanned images with no extractable text. If `extract_pdf_text()` returns an empty string:

```python
if pdf_text is not None and len(pdf_text.strip()) == 0:
    pdf_text = "[PDF appears to be image-based with no extractable text. Assessment limited to form fields.]"
    pdf_extraction_failed = True
```

### 9B. Grok API timeout
If the Grok call takes significantly longer due to the larger prompt (PDF text), consider increasing the timeout. A 15-page PDF adds ~20,000 tokens — Grok should still respond within 30 seconds, but set the timeout to 60 seconds to be safe.

### 9C. Grok rate limiting
At expected submission volumes (low), this shouldn't be an issue. Log the response time for monitoring:

```python
import time

start_time = time.time()
# ... Grok API call ...
elapsed = time.time() - start_time
print(f"[GROK] Response time: {elapsed:.1f}s, PDF chars: {len(pdf_text)}")
```

### 9D. self-certification fields in formData
The 8 new checkbox boolean fields are included in formData but are NOT sent to Grok (the prompt uses PDF text instead). They are included in the GitHub issue self-certification section only. The server should still read them from formData for the issue markdown, with defaults of `False` for any missing fields.

---

## 10. What NOT To Change in Phase 6b

- Do NOT modify the form fields or step structure (Phase 6a is locked)
- Do NOT modify the criteria accordion
- Do NOT change the PDF upload, validation, or storage location
- Do NOT change the API endpoint path or method
- Do NOT change the existing examiner email notification flow

---

## Verification Checklist (for Graham)

After applying these changes, confirm:

### Basic functionality:
- [ ] Server starts without errors
- [ ] pdfplumber is installed and importable
- [ ] Make a test submission with a real multi-page PDF
- [ ] No server crash during PDF extraction
- [ ] Grok API call succeeds (check server logs for response time)

### Scorecard quality:
- [ ] GitHub issue contains new scorecard with 9 criteria
- [ ] Each criterion shows one of: ✅ Pass, ⚠️ Conditional Pass, ⚠️ Conditional Fail, ❌ Fail
- [ ] Compliance Verdict and Worth Checking Verdict both present
- [ ] Summary paragraph present (3-5 sentences, sounds like a structural reviewer)
- [ ] Notes reference actual PDF content, not just form fields

### Verdicts and labels:
- [ ] Issue has correct labels based on verdicts
- [ ] If COMPLIANT: label is "AI Pre-Check: Compliant"
- [ ] If NON_COMPLIANT + WORTH_CHECKING: label is "AI Pre-Check: Worth Checking"
- [ ] If NOT_WORTH_CHECKING: label is "AI Pre-Check: Structural Issues"

### Frontend:
- [ ] Success screen shows appropriate verdict message
- [ ] "View Issue on GitHub" link still works
- [ ] Submission succeeds even if verdict is negative

### Edge cases:
- [ ] Test with a very short PDF (1 page) — should work
- [ ] Test with a text-free PDF (scanned image) — should gracefully degrade
- [ ] Verify server logs show Grok response time and PDF character count
- [ ] Previous test issues are unaffected

### IMPORTANT — Do NOT run the Cross-Domain test harness yet.
That is Phase 6c. Get the mechanics working first, then we validate accuracy.

---

*Phase 6b of 6c — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
