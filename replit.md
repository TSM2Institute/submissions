# TSM2 Institute Submission Portal

**Version 1.0** — May 2026

## Overview

This is a submission portal for the TSM2 Institute for Cosmology. The application allows users to submit scientific papers or proposals through a simplified web interface using a **Binary Structural Compliance Model**. Submissions are automatically created as GitHub Issues with attached PDF documents for review.

**Key Features:**
- Binary structural compliance outcomes: Compliant or Non-Compliant (no partial acceptance)
- Structural compliance does not constitute scientific validation or endorsement
- Mandatory PDF upload as the authoritative record
- User personal details kept private (not posted to GitHub)
- AI compliance pre-check using Grok API (9-criteria structural scorecard)
- 6-step form with criteria self-certification checkboxes
- Criteria declaration checkboxes (6 structural criteria confirmed by submitter)
- Auto-labelling of GitHub issues (Pending Review + screening result)
- Email notification to Institute Director with private submitter details

**Status:** Fully functional and published

## User Preferences

Preferred communication style: Simple, everyday language.

## Project Structure

```
├── index.html          # Frontend (single-page app with 6-step form)
├── start.sh            # Auto-restart wrapper for server.py
├── server.py           # Backend (Python HTTP server + API endpoint)
├── replitmail.py       # Email notification utility (Replit Mail API)
├── replit.md           # Replit-specific project documentation (this file)
├── README.md           # Full project documentation for Git
├── .gitignore          # Excludes uploads, cache, logs from Git
├── public/
│   └── files/
│       └── governance.md   # Governance protocol (Steps 10-14 + 9 criteria list)
└── uploads/            # PDF storage directory (gitignored)
```

## System Architecture

### Frontend Architecture
- **Static HTML** with Tailwind CSS for styling (loaded via CDN)
- **Alpine.js** for lightweight client-side interactivity (loaded via CDN)
- **Design Pattern**: Single-page application with a cosmic/space-themed visual design
- **Typography**: Inter font family from Google Fonts

### Backend Architecture
- **Python HTTP Server**: Custom `SimpleHTTPRequestHandler` extension
- **API Endpoint**: `/api/submit` handles POST multipart/form-data submissions
- **PDF Storage**: Local `/uploads/` folder with public URLs
- **PDF Validation**: Extension check, magic bytes verification, 100MB size limit, filename sanitization
- **AI Integration**: Grok API (multimodal — `grok-4` when page images are available, falls back to `grok-3-mini` text-only) for 9-criteria structural compliance pre-checking (evaluates structure, not scientific truth)
- **PDF Vision**: PyMuPDF renders each PDF page to a 200 DPI PNG, sent alongside the extracted text in the Grok call. Capped at 50 pages per submission; text extraction is unaffected by this cap. PyMuPDF is AGPL — acceptable for the Institute's non-commercial public-source use; reassess if the platform ever moves to commercial SaaS.
- **GitHub Integration**: Creates Issues via GitHub API in `TSM2Institute/submissions`
- **Email Integration**: Replit Mail sends submitter details privately to Institute Director

### Form Structure (6 Steps)
1. **Your Information** - Name, Email, Organization (private, not in GitHub issue)
2. **Submission Details** - Title, Core Claim, Primary Scale
3. **Criteria Confirmation** - 6 checkboxes confirming PDF addresses criteria 2,3,4,5,6,9
4. **Falsifiability Condition** - Required testable falsification criteria
5. **Document Upload** - Mandatory PDF (up to 100MB)
6. **Declaration** - Binary structural compliance acknowledgment

### AI Compliance Criteria (9-criteria scorecard)
1. Explicit Claim — singular, clear, non-compound (assessed from form)
2. Key Term Definitions — submitter self-certification
3. Declared Assumptions — submitter self-certification
4. Stated Mechanism — submitter self-certification
5. Energy Conservation — submitter self-certification
6. Empirical Anchor — submitter self-certification
7. Falsifiability — testable and specific (assessed from form)
8. Scale Consistency — physical scale stated (assessed from form)
9. Category Integrity — physical causation, not metaphor (assessed from form)

Per-criterion statuses: PASS / DECLARED / FLAG / MISSING
Overall outcomes: PASSED / NEEDS REVIEW / UNAVAILABLE

### Data Flow
1. User fills out 6-step form with criteria confirmation and PDF attachment
2. Personal info collected but kept private
3. Form data sent as multipart/form-data to `/api/submit`
4. Server validates PDF (extension, header, size, filename sanitization)
5. Server saves PDF to `/uploads/` folder with unique prefix
6. Grok AI performs 9-criteria scorecard compliance check on form fields
7. Server creates GitHub Issue with submission details + PDF link + scorecard
8. AI scorecard (PASSED/NEEDS REVIEW/UNAVAILABLE) included in issue
9. GitHub labels auto-applied (Pending Review + screening result)
10. Email notification sent to Institute Director with private submitter details
11. Submitter email content built and logged server-side (external email delivery pending — Replit Mail is limited to verified internal address; external SMTP service TBD)

### Static File Serving
- The Python server doubles as a static file server for the HTML frontend
- Cache-control headers prevent stale content
- Public files (like governance documentation) are stored in `/public/files/`
- PDFs are stored in `/uploads/` and served with public URLs

## External Dependencies

### Third-Party Services
- **GitHub API**: Creates issues for tracking submissions
  - Repository: `TSM2Institute/submissions`
  - Requires `GITHUB_PAT` environment variable
- **Grok API**: AI compliance pre-checking (multimodal)
  - Endpoint: `https://api.x.ai/v1/chat/completions`
  - Model: `grok-4` when page images are sent (default path), `grok-3-mini` fallback for text-only
  - Multimodal payload: rendered PNG page images + extracted text + structural prompt
  - Requires `GROK_API_KEY` environment variable
  - Note: Requests must include a `User-Agent` header (Cloudflare blocks requests without one)
- **Replit Mail**: Email notifications for submitter details
  - Sends to Institute Director's verified Replit email
  - Uses internal Replit authentication (no API key needed)
  - Implemented in `replitmail.py`

### CDN Dependencies
- **Tailwind CSS**: `https://cdn.tailwindcss.com`
- **Alpine.js**: `https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js`
- **Alpine.js Collapse Plugin**: `https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js`
- **Google Fonts**: Inter font family

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `GITHUB_PAT` | GitHub Personal Access Token for creating issues |
| `GROK_API_KEY` | Grok API key for AI compliance checking |

## Deployment

- **Target**: Autoscale
- **Run command**: `bash start.sh`
- **Port**: 5000 (internal) mapped to 80 (external)

## Change History

### Portal Update v1.0 (May 2026)

**Phase 1: Language & Legal Protection**
- "Binary Compliance" updated to "Binary Structural Compliance" throughout
- Added disclaimers: structural compliance ≠ scientific validation
- Added criteria reference accordion (10 criteria, #10 marked examiner-only)
- Added "Return to TSM2 Institute" navigation link

**Phase 2: Form Expansion**
- Form expanded from 5 steps to 6 steps
- New Step 3: Criteria Confirmation (6 self-certification checkboxes)
- Criteria 2, 3, 4, 5, 6, 9 now captured via submitter declaration
- GitHub issue includes criteria self-certification section

**Phase 3: AI Prompt Upgrade**
- Grok prompt upgraded from 4 checks to 9-criteria structural scorecard
- Response format: per-criterion status (PASS/DECLARED/FLAG/MISSING) with notes
- GitHub issue includes full scorecard table
- Fallback handling for API errors and legacy response formats

**Phase 4: GitHub Labels & Notifications**
- Auto-labels applied on submission: Pending Review + screening result
- Submitter email content built (PASSED/NEEDS REVIEW/UNAVAILABLE templates)
- External email delivery pending (Replit Mail limited to internal; external service TBD)
- Improved Grok API error logging with `[GROK ERROR]` prefix and response body
- Fixed Grok 403 errors by adding `User-Agent` header (Cloudflare requirement)

**Phase 5: Documentation & Version Stamp**
- governance.md updated with explicit 9-criteria list + Criterion 10 (examiner-only)
- README.md and replit.md fully updated to reflect current system
- Version stamped as v1.0

### Initial Build (January 2026)
- Reduced from 11 steps to 5 steps
- Binary structural compliance model (Compliant / Non-Compliant)
- Mandatory PDF upload as authoritative record
- User personal details kept private
- Added Grok AI compliance pre-check
- Added multipart form data handling for PDF uploads
- Added `/uploads/` folder for PDF storage
- Added cache-control headers to prevent stale content
- Added PDF validation (file type, size limit, header check)
- Added filename sanitization for security
- Added Replit Mail email notifications for submitter details
- Added `start.sh` auto-restart wrapper
- Created comprehensive README.md for Git repository
