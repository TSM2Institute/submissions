# TSM2 Institute Submission Portal

## Overview

This is a submission portal for the TSM2 Institute for Cosmology. The application allows users to submit scientific papers or proposals through a web interface, which are then automatically created as GitHub Issues in the repository for tracking and review.

The system follows a governance protocol where submissions go through compliance checking and examiner review before being registered.

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
- **Integration Pattern**: Submissions are converted to GitHub Issues via the GitHub API
- **Authentication**: Uses GitHub Personal Access Token (PAT) stored in environment variable `GITHUB_PAT`

### Data Flow
1. User fills out submission form on the frontend
2. Form data is sent as JSON to `/api/submit`
3. Server creates a GitHub Issue with the submission data
4. Issue is labeled with `submission` and `needs-triage` for workflow tracking

### Static File Serving
- The Python server doubles as a static file server for the HTML frontend
- Public files (like governance documentation) are stored in `/public/files/`

## External Dependencies

### Third-Party Services
- **GitHub API**: Used to create issues for tracking submissions
  - Repository: `TSM2Institute/submissions`
  - Requires `GITHUB_PAT` environment variable with appropriate permissions

### CDN Dependencies
- **Tailwind CSS**: `https://cdn.tailwindcss.com`
- **Alpine.js**: `https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js`
- **Alpine.js Collapse Plugin**: `https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js`
- **Google Fonts**: Inter font family

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `GITHUB_PAT` | GitHub Personal Access Token for creating issues |