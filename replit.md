# TSM2 Institute Submission Portal

## Overview

This is a submission portal for the TSM2 Institute for Cosmology. The application allows users to submit scientific papers or proposals through a simplified web interface using a **Binary Compliance Model**. Submissions are automatically created as GitHub Issues with attached PDF documents for review.

**Key Features:**
- Binary compliance outcomes: Compliant or Non-Compliant (no partial acceptance)
- Mandatory PDF upload as the authoritative record
- User personal details kept private (not posted to GitHub)
- AI compliance pre-check using Grok API
- 5-step simplified form

**Status:** Fully functional with new simplified form

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Static HTML** with Tailwind CSS for styling (loaded via CDN)
- **Alpine.js** for lightweight client-side interactivity (loaded via CDN)
- **Design Pattern**: Single-page application with a cosmic/space-themed visual design
- **Typography**: Inter font family from Google Fonts

### Backend Architecture
- **Python HTTP Server**: Custom `SimpleHTTPRequestHandler` extension
- **API Endpoint**: `/api/submit` handles POST requests for form submissions
- **PDF Storage**: Local `/uploads/` folder with public URLs
- **AI Integration**: Grok API for compliance pre-checking
- **GitHub Integration**: Creates Issues via GitHub API

### Form Structure (5 Steps)
1. **Your Information** - Name, Email, Organization (private, not in GitHub issue)
2. **Submission Details** - Title, Core Claim, Primary Scale
3. **Falsifiability Condition** - Required testable falsification criteria
4. **Document Upload** - Mandatory PDF (up to 100MB)
5. **Declaration** - Binary compliance acknowledgment

### Data Flow
1. User fills out simplified 5-step form with PDF attachment
2. Personal info collected but kept private
3. Form data sent as multipart/form-data to `/api/submit`
4. Server saves PDF to `/uploads/` folder
5. Grok AI performs quick compliance check on form fields
6. Server creates GitHub Issue with submission details + PDF link
7. AI compliance result included in issue
8. Email notification sent to Institute Director with private submitter details

### Static File Serving
- The Python server doubles as a static file server for the HTML frontend
- Public files (like governance documentation) are stored in `/public/files/`
- PDFs are stored in `/uploads/` and served with public URLs

## External Dependencies

### Third-Party Services
- **GitHub API**: Creates issues for tracking submissions
  - Repository: `TSM2Institute/submissions`
  - Requires `GITHUB_PAT` environment variable
- **Grok API**: AI compliance pre-checking
  - Requires `GROK_API_KEY` environment variable
- **Replit Mail**: Email notifications for submitter details
  - Sends to Institute Director's verified Replit email
  - Uses internal Replit authentication (no API key needed)

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

## Recent Changes (January 2026)

### Form Simplification
- Reduced from 11 steps to 5 steps
- Binary compliance model (Compliant / Non-Compliant)
- Mandatory PDF upload as authoritative record
- User personal details kept private
- Added Grok AI compliance pre-check

### Technical Updates
- Added multipart form data handling for PDF uploads
- Added `/uploads/` folder for PDF storage
- Integrated Grok API for compliance checking
- Added cache-control headers to prevent stale content
- Added PDF validation (file type, size limit, header check)
- Added filename sanitization for security
- Added Replit Mail email notifications for submitter details
- Cleaned up deployment config (removed conflicting port 80 workflow)
