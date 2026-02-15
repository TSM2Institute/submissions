# TSM2 Institute for Cosmology – Submission Portal

A web-based submission portal for the TSM2 Institute for Cosmology. Scientists and researchers submit structured theoretical claims through a streamlined form, with mandatory PDF documentation. Submissions are evaluated using a **Binary Compliance Model** — each submission is either **Compliant** or **Non-Compliant**, with no partial acceptance.

---

## How It Works

### Submission Process

1. **Fill out the form** — A 5-step form collects the submission details
2. **Attach a PDF** — A mandatory PDF document serves as the authoritative record
3. **AI Pre-Check** — Grok AI performs an automated compliance screening
4. **GitHub Issue Created** — The submission is logged as a GitHub Issue with the PDF link
5. **Email Notification** — The Institute Director receives a private email with the submitter's personal details

### The 5-Step Form

| Step | Name | What's Collected |
|------|------|------------------|
| 1 | **Your Information** | Name, Email, Organization *(kept private)* |
| 2 | **Submission Details** | Title, Core Claim, Primary Scale |
| 3 | **Falsifiability Condition** | A testable condition that could disprove the claim |
| 4 | **Document Upload** | Mandatory PDF attachment (up to 100MB) |
| 5 | **Declaration** | Acknowledgment of binary compliance rules |

### Privacy

- Submitter personal details (name, email, organization) are **never** posted to the public GitHub issue
- Personal details are sent privately via email to the Institute Director only
- The GitHub issue contains only the scientific content and PDF link

---

## AI Compliance Pre-Check

The system uses Grok AI (via the xAI API) to perform an automated compliance screening before the submission is logged. The AI evaluates 4 criteria:

| # | Criterion | Description |
|---|-----------|-------------|
| 1 | **Clear, single explicit claim** | The claim must not be compound or vague |
| 2 | **Testable falsifiability condition** | Must specify how the claim could be proven wrong |
| 3 | **No rhetorical or emotive language** | Scientific, objective tone required |
| 4 | **Physical or cosmological scale stated** | e.g., quantum, stellar, galactic, cosmic |

### Outcomes

- **PASSED** — All criteria met; submission proceeds normally
- **NEEDS REVIEW** — One or more criteria flagged; submission still proceeds but is marked for closer review

The AI result is included in the GitHub issue when available. This is a **pre-check only** — the final compliance decision is made by a human examiner.

> **Note:** The AI pre-check requires a valid `GROK_API_KEY`. If the key is not configured, submissions will still proceed but without AI compliance data in the issue.

---

## What Gets Stored in the GitHub Issue

Each submission creates a GitHub Issue in the `TSM2Institute/submissions` repository:

**Issue Title:** `[TSM2-SUB] {submission title}`

**Issue Body Contains:**
- Submission title
- Primary scale
- Core claim text
- Falsifiability condition
- PDF download link (clickable)
- File size
- Declaration confirmations
- AI Compliance Pre-Check result (PASSED / NEEDS REVIEW + explanation)

**Not Included (Private):**
- Submitter's name
- Submitter's email
- Submitter's organization

---

## Examiner Workflow

1. Examiner receives **GitHub notification** when a new issue is created
2. Examiner receives **private email** (via Replit Mail) with submitter details
3. Examiner reviews the GitHub issue content and downloads the PDF
4. Examiner uses the AI compliance result as initial guidance
5. Examiner makes the **final binary decision**: Compliant or Non-Compliant
6. Further governance steps (registration, archiving) follow the [Governance Protocol](public/files/governance.md)

---

## Project Structure

```
├── index.html          # Frontend (single-page app with 5-step form)
├── server.py           # Backend (Python HTTP server + API)
├── replitmail.py       # Email notification utility (Replit Mail integration)
├── replit.md           # Replit-specific project documentation
├── README.md           # This file
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
| **AI** | Grok API (xAI) via `grok-3-mini` model |
| **Issue Tracking** | GitHub Issues API |
| **Email** | Replit Mail (internal service) |
| **PDF Storage** | Local `/uploads/` directory with public URLs |
| **Hosting** | Replit (autoscale deployment) |
| **Font** | Inter (Google Fonts) |

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITHUB_PAT` | Yes | GitHub Personal Access Token for creating issues in `TSM2Institute/submissions` |
| `GROK_API_KEY` | Yes | xAI API key for Grok AI compliance checking |

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
    "message": "Submission meets all structural requirements."
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

- AI Compliance Confirmation
- Assignment to Qualified Registered Examiner
- Examiner Confirmation or Return
- Sequential Registration Number Assignment
- Archival Lock & Public Record

---

## Deployment

The application is deployed on Replit using autoscale deployment:

- **Run command:** `python server.py`
- **Port:** 5000 (internal) mapped to 80 (external)
- **Target:** Autoscale

---

*TSM2 Institute for Cosmology*
