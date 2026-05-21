# PHASE 8a + 8b — PDF Storage Migration & Scale Labels

## Context for Builder

This is Phase 8a+8b of the TSM2 Submission Portal update. Phase 7 (email) is complete and verified.

Phase 8a migrates PDF storage from Replit's local `/uploads/` directory to the GitHub repository itself, giving every submission a permanent, publicly accessible PDF link. Phase 8b adds scale labels to GitHub issues for search filtering.

Both are server.py changes. No frontend changes.

---

## PART A: PDF Storage Migration to GitHub

### Current Problem

PDFs are saved to `/uploads/` on Replit. The URL in the GitHub issue points to the Replit dev environment (e.g., `https://xxxxx.riker.replit.dev/uploads/file.pdf`). This link breaks when the app restarts, redeploys, or is accessed externally.

### Solution

After saving the PDF locally (still needed for text extraction + vision rendering), upload it to the GitHub repository via the Contents API. The file is committed to a `/pdfs/` directory in the repo. The permanent URL is used in the GitHub issue body instead of the Replit URL.

### Implementation

#### Step 1: Upload function

Add a function to upload a file to the GitHub repo:

```python
import base64
import json
import urllib.request

def upload_pdf_to_github(local_path, filename, github_pat):
    """Upload a PDF to the GitHub repo and return the permanent URL.
    
    Args:
        local_path: path to the PDF file on local disk
        filename: the sanitized filename (with unique prefix)
        github_pat: GitHub Personal Access Token
    
    Returns:
        (permanent_url, success) tuple
        permanent_url: raw.githubusercontent.com URL if successful, None if failed
        success: boolean
    """
    try:
        # Read and base64-encode the file
        with open(local_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        # GitHub Contents API endpoint
        api_url = f"https://api.github.com/repos/TSM2Institute/submissions/contents/pdfs/{filename}"
        
        payload = json.dumps({
            "message": f"Upload submission PDF: {filename}",
            "content": content_b64
        }).encode("utf-8")
        
        req = urllib.request.Request(
            api_url,
            data=payload,
            method="PUT",
            headers={
                "Authorization": f"token {github_pat}",
                "Content-Type": "application/json",
                "User-Agent": "TSM2-Submission-Portal",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            # The download_url is the permanent raw URL
            permanent_url = result.get("content", {}).get("download_url", None)
            
            if permanent_url:
                print(f"[GITHUB PDF] Uploaded: {permanent_url}")
                return permanent_url, True
            else:
                print(f"[GITHUB PDF] Upload succeeded but no download_url in response")
                return None, False
                
    except Exception as e:
        print(f"[GITHUB PDF ERROR] Failed to upload {filename}: {e}")
        return None, False
```

#### Step 2: Integrate into submission flow

In the submission handler, AFTER the PDF is saved locally and AFTER text extraction + vision rendering, but BEFORE creating the GitHub issue:

```python
# Upload PDF to GitHub for permanent storage
permanent_pdf_url, pdf_upload_success = upload_pdf_to_github(
    local_path=saved_pdf_path,
    filename=sanitized_filename,  # the unique-prefixed filename already used
    github_pat=os.environ.get("GITHUB_PAT", "")
)

# Use permanent URL if upload succeeded, fall back to local URL if not
if pdf_upload_success and permanent_pdf_url:
    pdf_link_url = permanent_pdf_url
else:
    # Fallback to local Replit URL (existing behavior)
    pdf_link_url = f"{base_url}/uploads/{sanitized_filename}"
    print("[GITHUB PDF] Falling back to local Replit URL for PDF link")
```

#### Step 3: Use the permanent URL in the GitHub issue

Replace whatever variable currently holds the PDF URL in the issue body markdown with `pdf_link_url`. The issue body should show:

```markdown
- **PDF Attached:** [{original_filename}]({pdf_link_url})
```

Where `pdf_link_url` is now `https://raw.githubusercontent.com/TSM2Institute/submissions/main/pdfs/{filename}`.

#### Step 4: Handle duplicate filenames

The unique prefix already added to filenames (from Phase 1 era) prevents collisions. If for some reason the file already exists in the repo (409 Conflict response), the upload function should handle it gracefully:

```python
except urllib.error.HTTPError as e:
    if e.code == 422:  # Unprocessable Entity — file already exists
        # Construct the URL anyway (file is already there)
        permanent_url = f"https://raw.githubusercontent.com/TSM2Institute/submissions/main/pdfs/{filename}"
        print(f"[GITHUB PDF] File already exists: {permanent_url}")
        return permanent_url, True
    else:
        print(f"[GITHUB PDF ERROR] HTTP {e.code}: {e.read().decode()[:500]}")
        return None, False
```

#### Step 5: Local file retention

Keep the local `/uploads/` copy. It's needed for:
- Text extraction (pdfplumber)
- Vision rendering (PyMuPDF)

These happen BEFORE the GitHub upload. The local copy can optionally be deleted after successful GitHub upload to save Replit disk space, but this is not required. Builder's choice.

### What This Changes

| Before | After |
|--------|-------|
| PDF stored on Replit `/uploads/` only | PDF stored on Replit (temp) + GitHub repo (permanent) |
| PDF link: `https://xxxxx.riker.replit.dev/uploads/file.pdf` | PDF link: `https://raw.githubusercontent.com/TSM2Institute/submissions/main/pdfs/file.pdf` |
| Link breaks when Replit restarts | Link is permanent |

---

## PART B: Scale Labels

### Purpose

Add a label for the submission's primary scale to the GitHub issue. This enables filtering on the future search page.

### Implementation

In the auto-labelling section of `server.py` (where `Pending Review` and the compliance label are applied), add the scale label:

```python
# Map form scale values to GitHub labels
SCALE_LABELS = {
    "Quantum": "Scale: Quantum",
    "Atomic/Molecular": "Scale: Atomic/Molecular",
    "Planetary": "Scale: Planetary",
    "Stellar": "Scale: Stellar",
    "Galactic": "Scale: Galactic",
    "Cosmological": "Scale: Cosmic",
    "Multi-Scale": "Scale: Multi-Scale",
    "Other": "Scale: Other"
}

# Get the scale label
primary_scale = form_data.get("primary_scale", "")
scale_label = SCALE_LABELS.get(primary_scale, None)

# Add to labels list
labels = ["Pending Review"]  # always applied
labels.append(compliance_label)  # AI verdict label

if scale_label:
    labels.append(scale_label)
```

### Label Colors (for Graham to set manually in GitHub Settings → Labels)

| Label | Color (hex) |
|-------|-------------|
| `Scale: Quantum` | `#6A0DAD` (purple) |
| `Scale: Atomic/Molecular` | `#1B4F72` (dark blue) |
| `Scale: Planetary` | `#2E86C1` (blue) |
| `Scale: Stellar` | `#F39C12` (amber) |
| `Scale: Galactic` | `#E74C3C` (red) |
| `Scale: Cosmic` | `#8E44AD` (violet) |
| `Scale: Multi-Scale` | `#27AE60` (green) |
| `Scale: Other` | `#95A5A6` (grey) |

These don't need to be created in advance — GitHub auto-creates them on first use (without custom colors). Graham can set the colors manually afterward.

---

## What NOT To Change in Phase 8a+8b

- Do NOT modify index.html or the frontend
- Do NOT modify the Grok AI prompt
- Do NOT modify the email system (Phase 7)
- Do NOT modify the PDF validation, text extraction, or vision pipeline
- Do NOT change the API endpoint

---

## Verification Checklist (for Graham)

### PDF Storage (8a):
- [ ] Make a test submission with a real PDF
- [ ] Check the GitHub repo — PDF should appear in `/pdfs/` directory
- [ ] GitHub issue PDF link should start with `https://raw.githubusercontent.com/...`
- [ ] Click the PDF link in the GitHub issue — PDF should download/display
- [ ] Restart the Replit app — PDF link should still work (permanent URL)
- [ ] Check server logs for `[GITHUB PDF] Uploaded:` message
- [ ] If GitHub upload fails, submission still succeeds with fallback local URL

### Scale Labels (8b):
- [ ] Test submission has a scale label in the GitHub issue sidebar (e.g., `Scale: Cosmic`)
- [ ] Scale label matches what was selected in the form
- [ ] Existing labels (Pending Review, compliance label) still applied correctly
- [ ] Set label colors manually in GitHub Settings → Labels

### Email:
- [ ] Submitter email still arrives (Phase 7 not broken)
- [ ] Examiner email still arrives
- [ ] PDF link in emails uses the permanent GitHub URL (not the Replit URL)

---

*Phase 8a + 8b — TSM2 Submission Portal Update*
*Planner: Claude (Anthropic) — Builder: Replit Claude*
