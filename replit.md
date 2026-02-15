# TSM2 Institute Submission Portal

## Overview

This is a submission portal for the TSM2 Institute for Cosmology. The application allows users to submit scientific papers or proposals through a simplified web interface using a **Binary Compliance Model**. Submissions are automatically created as GitHub Issues with attached PDF documents for review.

**Key Features:**
- Binary compliance outcomes: Compliant or Non-Compliant (no partial acceptance)
- Mandatory PDF upload as the authoritative record
- User personal details kept private (not posted to GitHub)
- AI compliance pre-check using Grok API (4 criteria)
- 5-step simplified form
- Email notification to Institute Director with private submitter details

**Status:** Fully functional and published

## User Preferences

Preferred communication style: Simple, everyday language.

## Project Structure

```
├── index.html          # Frontend (single-page app with 5-step form)
├── server.py           # Backend (Python HTTP server + API endpoint)
├── replitmail.py       # Email notification utility (Replit Mail API)
├── replit.md           # Replit-specific project documentation (this file)
├── README.md           # Full project documentation for Git
├── .gitignore          # Excludes uploads, cache, logs from Git
├── public/
│   └── files/
│       └── governance.md   # Governance protocol (Steps 10-14)
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
- **AI Integration**: Grok API (`grok-3-mini`) for compliance pre-checking
- **GitHub Integration**: Creates Issues via GitHub API in `TSM2Institute/submissions`
- **Email Integration**: Replit Mail sends submitter details privately to Institute Director

### Form Structure (5 Steps)
1. **Your Information** - Name, Email, Organization (private, not in GitHub issue)
2. **Submission Details** - Title, Core Claim, Primary Scale
3. **Falsifiability Condition** - Required testable falsification criteria
4. **Document Upload** - Mandatory PDF (up to 100MB)
5. **Declaration** - Binary compliance acknowledgment

### AI Compliance Criteria (4 checks)
1. Clear, single explicit claim (not compound or vague)
2. Testable falsifiability condition provided
3. No rhetorical or emotive language
4. Physical or cosmological scale stated

### Data Flow
1. User fills out simplified 5-step form with PDF attachment
2. Personal info collected but kept private
3. Form data sent as multipart/form-data to `/api/submit`
4. Server validates PDF (extension, header, size, filename sanitization)
5. Server saves PDF to `/uploads/` folder with unique prefix
6. Grok AI performs compliance check on form fields (4 criteria)
7. Server creates GitHub Issue with submission details + PDF link
8. AI compliance result (PASSED/NEEDS REVIEW) included in issue
9. Email notification sent to Institute Director with private submitter details

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
- **Grok API**: AI compliance pre-checking
  - Endpoint: `https://api.x.ai/v1/chat/completions`
  - Model: `grok-3-mini`
  - Requires `GROK_API_KEY` environment variable
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
- **Run command**: `python server.py`
- **Port**: 5000 (internal) mapped to 80 (external)

## Recent Changes (January 2026)

### Form Simplification
- Reduced from 11 steps to 5 steps
- Binary compliance model (Compliant / Non-Compliant)
- Mandatory PDF upload as authoritative record
- User personal details kept private
- Added Grok AI compliance pre-check (4 criteria)

### Technical Updates
- Added multipart form data handling for PDF uploads
- Added `/uploads/` folder for PDF storage
- Integrated Grok API for compliance checking
- Added cache-control headers to prevent stale content
- Added PDF validation (file type, size limit, header check)
- Added filename sanitization for security
- Added Replit Mail email notifications for submitter details
- Cleaned up deployment config (removed conflicting port 80 workflow)
- Added .gitignore for uploads, cache, and temp files
- Created comprehensive README.md for Git repository
