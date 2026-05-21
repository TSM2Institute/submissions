# PHASE 7 — External Email Notifications via SMTP

## Context for Builder

This is Phase 7 of the TSM2 Submission Portal update. Phase 6 (AI pre-check calibration + vision) is complete.

Phase 7 replaces the Replit Mail system with proper SMTP email sending through the Institute's email server. This enables:
1. Email notifications to submitters (at their provided email address)
2. Email notifications to the examiner/director (at the Institute inbox)

Both emails are sent from `info@tsm2.org`.

---

## 1. SMTP Configuration

### Server Details

| Setting | Value |
|---------|-------|
| SMTP Hostname | `smtp.hostedemail.com` |
| Port | `587` |
| Encryption | TLS (STARTTLS) |
| Authentication | Required |
| Username | `info@tsm2.org` |
| Password | Read from Replit secret: `TSM2_INFO_EMAIL` |

### Implementation

Replace the Replit Mail integration (`replitmail.py` usage) with Python's built-in `smtplib` and `email` modules. No external packages needed.

Create a new utility function (can live in `server.py` or a new `emailutil.py` file — builder's choice on organisation):

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(to_address, subject, body_text, body_html=None):
    """Send an email via the Institute's SMTP server.
    
    Args:
        to_address: recipient email address (string)
        subject: email subject line (string)
        body_text: plain text body (string)
        body_html: optional HTML body (string) — if provided, sends multipart
    
    Returns:
        True if sent successfully, False otherwise
    """
    smtp_host = "smtp.hostedemail.com"
    smtp_port = 587
    smtp_user = "info@tsm2.org"
    smtp_pass = os.environ.get("TSM2_INFO_EMAIL", "")
    
    if not smtp_pass:
        print("[EMAIL ERROR] TSM2_INFO_EMAIL secret not configured")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = "TSM2 Institute <info@tsm2.org>"
        msg["To"] = to_address
        msg["Subject"] = subject
        
        # Always attach plain text
        msg.attach(MIMEText(body_text, "plain"))
        
        # Attach HTML if provided
        if body_html:
            msg.attach(MIMEText(body_html, "html"))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        print(f"[EMAIL] Sent to {to_address}: {subject}")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_address}: {e}")
        return False
```

### Error Handling

Email failures must NEVER block or fail a submission. The email is sent after the GitHub issue is created and labelled. If it fails, log the error and continue. The submission is already safely recorded in GitHub.

Run email sending in a background thread (same pattern used for label application):

```python
import threading

def send_email_async(to_address, subject, body_text, body_html=None):
    """Fire-and-forget email sending in a background thread."""
    thread = threading.Thread(
        target=send_email,
        args=(to_address, subject, body_text, body_html)
    )
    thread.daemon = True
    thread.start()
```

---

## 2. Submitter Email

Sent to the submitter's email address (`userInfo['email']`) after the GitHub issue is created.

### 2A. When AI verdict is COMPLIANT:

**Subject:** `TSM2 Institute — Submission Received: {submission_title}`

**Plain text body:**

```
Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Title: {submission_title}
Primary Scale: {primary_scale}
Date: {date}

AI STRUCTURAL PRE-CHECK: COMPLIANT
All 9 structural criteria were met.

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission is now pending review by a qualified examiner.
- Structural compliance does not constitute scientific validation or endorsement.
- You will be contacted if any further information is required.

You can view your submission at:
{issue_url}

Thank you for your submission.

TSM2 Institute for Cosmology
info@tsm2.org
```

### 2B. When AI verdict is NON_COMPLIANT:

**Subject:** `TSM2 Institute — Submission Received: {submission_title}`

**Plain text body:**

```
Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Title: {submission_title}
Primary Scale: {primary_scale}
Date: {date}

AI STRUCTURAL PRE-CHECK: NON-COMPLIANT
The automated screening identified structural gaps in the following criteria:

{for each NON_COMPLIANT criterion:}
- {criterion_name}: {reason}
  Correction required: {required_correction}

MINIMUM CORRECTIONS REQUIRED
{list the required_correction text for each failed criterion}

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission will still proceed to examiner review.
- The corrections listed above are structural requirements, not judgements on scientific merit.
- You may revise and resubmit at any time.

You can view the full assessment at:
{issue_url}

Thank you for your submission.

TSM2 Institute for Cosmology
info@tsm2.org
```

### 2C. When AI verdict is UNAVAILABLE:

**Subject:** `TSM2 Institute — Submission Received: {submission_title}`

**Plain text body:**

```
Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Title: {submission_title}
Primary Scale: {primary_scale}
Date: {date}

AI STRUCTURAL PRE-CHECK: UNAVAILABLE
The automated screening could not be completed at this time. This does not affect your submission — it will proceed directly to examiner review.

You can view your submission at:
{issue_url}

Thank you for your submission.

TSM2 Institute for Cosmology
info@tsm2.org
```

---

## 3. Examiner/Director Email

Sent to `info@tsm2.org` (the Institute inbox) after the GitHub issue is created. This replaces the current Replit Mail notification.

**Subject:** `[TSM2-SUB] New Submission: {submission_title} — {compliance_verdict}`

**Plain text body:**

```
New submission received.

SUBMISSION DETAILS
Title: {submission_title}
Primary Scale: {primary_scale}
Core Claim: {core_claim}
GitHub Issue: #{issue_number} — {issue_url}

SUBMITTER DETAILS (PRIVATE)
Name: {submitter_name}
Email: {submitter_email}
Organization: {submitter_organization}
Phone: {submitter_phone}
Website: {submitter_website}

AI PRE-CHECK RESULT: {compliance_verdict}

{if NON_COMPLIANT:}
Failed criteria:
{for each NON_COMPLIANT criterion:}
- {criterion_name}: {reason}

{end if}

Summary: {summary}

View full issue: {issue_url}
```

### Important Privacy Note

The examiner email is the ONLY place where submitter personal details appear. These details are NOT in the GitHub issue and NOT in the submitter email. This separation is already established — just maintain it.

---

## 4. Remove Replit Mail

After SMTP email is working:

1. Remove or comment out the Replit Mail import and calls in `server.py`
2. Remove or rename `replitmail.py` (keep the file in case of rollback, but don't import it)
3. Update the server-side email logging to note that emails are now sent via SMTP, not Replit Mail

If you prefer a safer approach: keep Replit Mail as a fallback. If SMTP fails, try Replit Mail. But honestly, if SMTP works, Replit Mail adds no value — it can't reach external addresses anyway.

---

## 5. Replit Secrets

Confirm the following secret is configured in the Replit environment:

| Secret Name | Value |
|-------------|-------|
| `TSM2_INFO_EMAIL` | The password for info@tsm2.org |

This should already be set by Graham. The builder just needs to reference it via `os.environ.get("TSM2_INFO_EMAIL")`.

---

## 6. What NOT To Change in Phase 7

- Do NOT modify the form fields or form structure
- Do NOT modify the Grok AI prompt
- Do NOT modify the GitHub issue format or content
- Do NOT modify the PDF upload, extraction, or vision pipeline
- Do NOT modify the auto-labelling logic
- Do NOT modify the frontend submit screen
- Do NOT change the API endpoint

---

## 7. Documentation Updates

Update `README.md` and `replit.md`:

- Replace all references to "Replit Mail" with "SMTP email (via Institute mail server)"
- Update the environment variables table:
  - Add `TSM2_INFO_EMAIL` — Institute email password for SMTP sending
  - Note that Replit Mail is no longer used
- Update the data flow section to mention both submitter and examiner emails
- Note: emails are sent from `info@tsm2.org` via `smtp.hostedemail.com` (TLS, port 587)

---

## Verification Checklist (for Graham)

### SMTP connectivity:
- [ ] Server starts without errors
- [ ] `TSM2_INFO_EMAIL` secret is configured in Replit
- [ ] No import errors for smtplib/email modules

### Submitter email:
- [ ] Make a test submission with YOUR email address as the submitter
- [ ] Receive the submitter email at your address
- [ ] Email comes from `info@tsm2.org` (or shows TSM2 Institute as sender)
- [ ] Subject line includes submission title
- [ ] Body includes submission reference (issue number, URL)
- [ ] Body includes AI verdict and corrections (if NON_COMPLIANT)
- [ ] GitHub issue link in email is clickable and works
- [ ] No submitter private details in the email body (name/org are fine — they're the recipient)

### Examiner email:
- [ ] Receive the examiner email at `info@tsm2.org`
- [ ] Email includes submitter's private details (name, email, org, phone, website)
- [ ] Email includes AI verdict summary
- [ ] Email includes GitHub issue link

### Failure handling:
- [ ] If SMTP fails (e.g., wrong password), submission still succeeds
- [ ] Error is logged in server console
- [ ] GitHub issue is created regardless of email status

### Cleanup:
- [ ] Replit Mail is no longer called
- [ ] README.md and replit.md updated

---

*Phase 7 — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
