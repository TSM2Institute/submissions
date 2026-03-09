# PHASE 4 — GitHub Auto-Labels & Submitter Email Notification

## Context for Builder

This is Phase 4 of the TSM2 Submission Portal update. Phases 1-3 are complete and verified.

Phase 4 adds two features:
1. **Automatic GitHub labels** applied when a submission issue is created
2. **Email notification to the submitter** confirming receipt and AI screening results

Both are server-side changes in `server.py`. No changes to `index.html` or the form.

---

## PART A: GitHub Auto-Labels

### Labels to Create in the Repository

First, ensure these labels exist in the `TSM2Institute/submissions` repository. If they don't exist, the server should create them via the GitHub API on first use, OR Graham can create them manually. Provide instructions for both approaches.

**Required labels:**

| Label | Color (hex) | Description |
|-------|-------------|-------------|
| `Pending Review` | `#0E8A16` (green) | Awaiting examiner review |
| `Screening: Passed` | `#1D76DB` (blue) | AI pre-check passed all criteria |
| `Screening: Needs Review` | `#E4E669` (yellow) | AI pre-check flagged one or more criteria |
| `Screening: Unavailable` | `#D93F0B` (orange) | AI pre-check could not be completed |

### Auto-Label Logic (server.py)

After creating the GitHub issue, apply labels based on the AI screening result.

**Logic:**

```
IF AI overall == "PASSED":
    Apply labels: ["Pending Review", "Screening: Passed"]
ELSE IF AI overall == "NEEDS REVIEW":
    Apply labels: ["Pending Review", "Screening: Needs Review"]
ELSE (AI unavailable/error):
    Apply labels: ["Pending Review", "Screening: Unavailable"]
```

**"Pending Review" is ALWAYS applied.** It's the base state for every new submission.

### GitHub API Call

After the issue is created (you already have the issue number), make a second API call to apply labels:

```
POST https://api.github.com/repos/TSM2Institute/submissions/issues/{issue_number}/labels
Authorization: token {GITHUB_PAT}
Content-Type: application/json

{
  "labels": ["Pending Review", "Screening: Passed"]
}
```

The GitHub API will auto-create labels if they don't exist, but they won't have the correct colors. It's better to pre-create them. Add a note in the code comments that Graham should create the labels manually in GitHub Settings → Labels if they don't exist with the correct colors.

### Error Handling

If the label API call fails, log the error but do NOT fail the submission. The issue is already created — labels are a nice-to-have, not a gate.

---

## PART B: Submitter Email Notification

### Purpose

Send an automated email to the submitter confirming their submission was received and showing the AI screening results. This is NOT an approval or rejection — it's a receipt with structural feedback.

### Email Recipient

The submitter's email address is available in `userInfo.email` (from the form's private data).

### Email Sending Method

**Option 1 (preferred):** If Replit Mail can send to external email addresses, use it. The existing `replitmail.py` module is already set up for the examiner notification.

**Option 2 (fallback):** If Replit Mail only sends to internal/verified Replit addresses, note this limitation in a code comment and skip the submitter email for now. Add a TODO comment: `# TODO: Submitter email requires external email service (e.g., SendGrid, Mailgun, or SMTP)`

**Try Option 1 first.** If it doesn't work, implement Option 2 and let Graham know.

### Email Content — SCREENING PASSED

```
Subject: TSM2 Institute — Submission Received [TSM2-SUB] {submission_title}

Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Submitted: {date}
Primary Scale: {primary_scale}

AI STRUCTURAL PRE-CHECK: PASSED
All 9 structural criteria were addressed.

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission is now pending review by a qualified examiner.
- Structural compliance does not constitute scientific validation or endorsement.
- You will be contacted if any further information is required.

Thank you for your submission.

TSM2 Institute for Cosmology
```

### Email Content — SCREENING NEEDS REVIEW

```
Subject: TSM2 Institute — Submission Received [TSM2-SUB] {submission_title}

Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Submitted: {date}
Primary Scale: {primary_scale}

AI STRUCTURAL PRE-CHECK: NEEDS REVIEW
The automated screening identified potential structural gaps:

{scorecard_summary — list only the criteria with FLAG or MISSING status}

For example:
- Criterion 1 (Explicit Claim): FLAG — Claim appears to contain multiple assertions.
- Criterion 7 (Falsifiability): FLAG — Condition may not be specifically testable.

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission will still proceed to examiner review.
- The examiner may contact you if revisions are needed.
- Structural compliance does not constitute scientific validation or endorsement.

Thank you for your submission.

TSM2 Institute for Cosmology
```

### Email Content — SCREENING UNAVAILABLE

```
Subject: TSM2 Institute — Submission Received [TSM2-SUB] {submission_title}

Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Submitted: {date}
Primary Scale: {primary_scale}

AI STRUCTURAL PRE-CHECK: UNAVAILABLE
The automated screening could not be completed at this time. This does not affect your submission — it will proceed directly to examiner review.

Please note:
- Your submission is now pending review by a qualified examiner.
- You will be contacted if any further information is required.

Thank you for your submission.

TSM2 Institute for Cosmology
```

### Implementation Notes

- Send the submitter email AFTER the GitHub issue is created and labels are applied (so you have the issue number)
- The submitter email is sent to `userInfo['email']`
- The examiner email (existing) continues to go to the Institute Director as before — do not change it
- If the email fails to send, log the error but do NOT fail the submission
- Do not include the submitter's private details in the GitHub issue (this rule is already in place — just don't break it)

---

## PART C: Grok API Key Check

Graham mentioned the Grok API key may be throwing errors. Add a small improvement:

### On server startup or first API call:

Add a more descriptive error log when the Grok API call fails. Include the HTTP status code and response body in the server log (NOT in the GitHub issue or email — just server-side logging for debugging).

```python
# Example
if response.status_code != 200:
    print(f"[GROK ERROR] Status: {response.status_code}, Body: {response.text[:500]}")
```

This helps Graham diagnose API key issues without digging through generic error messages.

---

## What NOT To Change in Phase 4

- Do NOT modify index.html or the form
- Do NOT change the Grok prompt (Phase 3 is locked)
- Do NOT change the GitHub issue markdown format
- Do NOT change the PDF upload or validation
- Do NOT change the existing examiner email notification

---

## Verification Checklist (for Graham)

After applying these changes, confirm:

- [ ] Make a test submission with a well-structured claim
- [ ] GitHub issue has correct labels applied (check issue sidebar)
- [ ] "Pending Review" label is present
- [ ] Screening result label matches AI outcome (Passed/Needs Review/Unavailable)
- [ ] Submitter receives email at the address they provided in the form
- [ ] Email content matches the appropriate template (Passed/Needs Review/Unavailable)
- [ ] Email does NOT contain private examiner information
- [ ] Examiner email still sends as before (unchanged)
- [ ] If Grok API errors, check server logs for descriptive error message
- [ ] Test with a deliberately vague claim — confirm "Needs Review" label and email
- [ ] Confirm submission still succeeds even if label or email fails

### If Replit Mail cannot send to external addresses:
- [ ] Builder has noted this in code comments
- [ ] TODO comment added for future email service integration
- [ ] Graham is aware external email service will be needed

---

*Phase 4 of 5 — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
