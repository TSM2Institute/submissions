# TSM2 Institute for Cosmology – Submission Portal

**Version 1.0** — May 2026

A web-based submission portal for the TSM2 Institute for Cosmology. Scientists and researchers submit structured theoretical claims through a streamlined form, with mandatory PDF documentation. Submissions are evaluated using a **Binary Structural Compliance Model** — each submission is either **Compliant** or **Non-Compliant**, with no partial acceptance. Structural compliance does not constitute scientific validation or endorsement.

---

## How It Works

### Submission Process

1. **Fill out the form** — A 6-step form collects the submission details and criteria self-certification
2. **Attach a PDF** — A mandatory PDF document serves as the authoritative record
3. **AI Pre-Check** — Grok AI performs an automated 9-criteria structural screening
4. **GitHub Issue Created** — The submission is logged as a GitHub Issue with the PDF link and scorecard
5. **Labels Applied** — GitHub labels are automatically applied based on the screening result
6. **Email Notification** — The Institute Director receives a private email with the submitter's personal details

### The 6-Step Form

| Step | Name | What's Collected |
|------|------|------------------|
| 1 | **Your Information** | Name, Email, Organization *(kept private)* |
| 2 | **Submission Details** | Title, Core Claim, Primary Scale |
| 3 | **Criteria Confirmation** | Self-certification that the PDF addresses criteria 2, 3, 4, 5, 6, and 9 |
| 4 | **Falsifiability Condition** | A testable condition that could disprove the claim |
| 5 | **Document Upload** | Mandatory PDF attachment (up to 100MB) |
| 6 | **Declaration** | Acknowledgment of binary structural compliance rules |

### Privacy

- Submitter personal details (name, email, organization) are **never** posted to the public GitHub issue
- Personal details are sent privately via email to the Institute Director only
- The GitHub issue contains only the scientific content and PDF link

---

## AI Structural Pre-Check

The AI pre-check uses Grok in multimodal mode, analyzing both extracted text (via `pdfplumber`) and rendered page images (via PyMuPDF, 200 DPI PNG, up to 50 pages per submission). This allows assessment of figures, diagrams, and equations that text extraction alone cannot capture. The AI evaluates 9 criteria:

| # | Criterion | Assessment Method |
|---|-----------|-------------------|
| 1 | Explicit Claim | Assessed from Core Claim field |
| 2 | Key Term Definitions | Submitter self-certification |
| 3 | Declared Assumptions | Submitter self-certification |
| 4 | Stated Mechanism | Submitter self-certification |
| 5 | Energy Conservation | Submitter self-certification |
| 6 | Empirical Anchor | Submitter self-certification |
| 7 | Falsifiability | Assessed from Falsifiability field |
| 8 | Scale Consistency | Assessed from Primary Scale + Core Claim |
| 9 | Category Integrity | Assessed from Core Claim field |

### Statuses

Each criterion receives one of:
- **PASS** — Criterion clearly met (assessed criteria)
- **DECLARED** — Submitter self-certified their PDF addresses this (self-certification criteria)
- **FLAG** — Potential issue identified, examiner should check
- **MISSING** — Not addressed or not certified

### Overall Outcomes

- **PASSED** — All criteria are PASS or DECLARED, no FLAGS or MISSING
- **NEEDS REVIEW** — One or more criteria are FLAG or MISSING

The AI pre-check evaluates structure, not scientific truth. This is a screening tool only — the final compliance decision is made by a qualified examiner.

> **Note:** The AI pre-check requires a valid `GROK_API_KEY`. If the key is not configured, submissions will still proceed but without AI compliance data in the issue.

---

## What Gets Stored in the GitHub Issue

Each submission creates a GitHub Issue in the `TSM2Institute/submissions` repository.

**Issue Title:** `[TSM2-SUB] {submission title}`

**Issue Body Contains:**
- Submission title, primary scale, core claim
- Falsifiability condition
- Criteria self-certification (6 checkboxes confirmed by submitter)
- PDF download link and file size
- Declaration confirmations
- AI Structural Pre-Check: 9-criteria scorecard with per-criterion status and notes

**Labels Applied Automatically:**
- `Pending Review` (always)
- `Screening: Passed` or `Screening: Needs Review` or `Screening: Unavailable`

**Not Included (Private):**
- Submitter's name, email, organization

---

## Examiner Workflow

1. Examiner receives **GitHub notification** when a new issue is created
2. Examiner receives **private email** with submitter details
3. Issue is labelled `Pending Review` plus the AI screening result
4. Examiner reviews the 9-criteria scorecard for initial guidance
5. Examiner reviews the submission content and downloads the PDF
6. Examiner applies **Criterion 10** ("Why Is This True?") as the primary integrity test
7. Examiner makes the **final binary decision**: Compliant or Non-Compliant
8. The Examiner decision applies only to structural compliance under Institute criteria and does not certify scientific correctness
9. Further governance steps (registration, archiving) follow the [Governance Protocol](public/files/governance.md)

---

## Project Structure

```
├── index.html          # Frontend (single-page app with 6-step form)
├── start.sh            # Auto-restart wrapper for server.py
├── server.py           # Backend (Python HTTP server + API)
├── emailutil.py        # SMTP email utility (Institute mail server)
├── replitmail.py       # Deprecated — retained for rollback only (not imported)
├── replit.md           # Replit-specific project documentation
├── README.md           # This file
├── .gitignore          # Excludes uploads, cache, logs from Git
├── public/
│   └── files/
│       └── governance.md   # Governance protocol documentation
└── uploads/            # PDF storage (not committed to Git)
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Static HTML, Tailwind CSS (CDN), Alpine.js (CDN) |
| **Backend** | Python 3.11 (`http.server`) |
| **AI** | Grok API (xAI) — `grok-4` multimodal when page images are rendered; `grok-3-mini` text-only fallback |
| **PDF Vision** | PyMuPDF (200 DPI PNG render, up to 50 pages); AGPL-licensed, acceptable for non-commercial Institute use |
| **Issue Tracking** | GitHub Issues API |
| **Email** | SMTP via `smtp.hostedemail.com` (TLS, port 587), authenticated as `info@tsm2.org`; uses Python stdlib `smtplib` |
| **PDF Storage** | Local `/uploads/` directory with public URLs |
| **Hosting** | Replit (autoscale deployment) |
| **Font** | Inter (Google Fonts) |

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITHUB_PAT` | Yes | GitHub Personal Access Token for creating issues in `TSM2Institute/submissions` |
| `GROK_API_KEY` | Yes | xAI API key for Grok AI compliance checking |
| `TSM2_INFO_EMAIL` | Yes | Password for `info@tsm2.org` — used for SMTP authentication against `smtp.hostedemail.com` (TLS, port 587) to send submitter confirmation and examiner notification emails |

These are stored as secrets in the Replit environment and are never exposed in code or logs.

---

## API Endpoint

### `POST /api/submit`

Accepts `multipart/form-data` with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Issue title (prefixed with `[TSM2-SUB]`) |
| `body` | string | Markdown-formatted issue body |
| `pdf` | file | PDF document (required, max 100MB) |
| `userInfo` | JSON string | `{name, email, organization}` — kept private |
| `formData` | JSON string | Form fields sent to Grok for compliance check |

**Success Response:**
```json
{
  "success": true,
  "html_url": "https://github.com/TSM2Institute/submissions/issues/42",
  "number": 42,
  "complianceCheck": {
    "compliant": true,
    "overall": "PASSED",
    "message": "The submission meets all structural criteria.",
    "criteria": [...]
  }
}
```

**Error Response:**
```json
{
  "error": "PDF document is required. Please attach a PDF file."
}
```

---

## PDF Validation

Uploaded PDFs are validated server-side:

- **File extension** must be `.pdf`
- **File header** must start with `%PDF` (magic bytes check)
- **File size** must not exceed 100MB
- **Filename** is sanitized (special characters removed, length limited)
- **Unique prefix** added to prevent filename collisions

---

## Governance Protocol

The full post-submission governance workflow is documented in [`public/files/governance.md`](public/files/governance.md). It covers:

- The 9 Structural Compliance Criteria (explicit list)
- Criterion 10 — Examiner Assessment Only
- AI Compliance Confirmation
- Assignment to Qualified Registered Examiner
- Examiner Confirmation or Return
- Sequential Registration Number Assignment
- Archival Lock & Public Record

---

## Deployment

The application is deployed on Replit using autoscale deployment:

- **Run command:** `bash start.sh`
- **Port:** 5000 (internal) mapped to 80 (external)
- **Target:** Autoscale

---

*TSM2 Institute for Cosmology*
