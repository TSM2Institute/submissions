import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import json
import os
import urllib.request
import urllib.error
import sys
import uuid
import cgi
import io
import time
import base64
import emailutil

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("[STARTUP] pdfplumber not installed; PDF text extraction will be disabled.", file=sys.stderr)

try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("[STARTUP] pymupdf not installed; PDF page-to-image rendering will be disabled.", file=sys.stderr)


GITHUB_REPO = "TSM2Institute/submissions"
GITHUB_PDF_BRANCH = "main"
GITHUB_PDF_DIR = "pdfs"

SCALE_LABELS = {
    "Quantum": "Scale: Quantum",
    "Atomic/Molecular": "Scale: Atomic/Molecular",
    "Planetary": "Scale: Planetary",
    "Stellar": "Scale: Stellar",
    "Galactic": "Scale: Galactic",
    "Cosmological": "Scale: Cosmic",
    "Multi-Scale": "Scale: Multi-Scale",
    "Other": "Scale: Other",
}


def upload_pdf_to_github(local_path, filename, github_pat):
    """Upload a PDF to the GitHub repo and return the permanent raw URL.

    Args:
        local_path: path to the PDF file on local disk
        filename: the sanitized filename (with unique prefix)
        github_pat: GitHub Personal Access Token

    Returns:
        (permanent_url, success) tuple. permanent_url is None on failure.
    """
    if not github_pat:
        print("[GITHUB PDF ERROR] GITHUB_PAT not configured; skipping upload", file=sys.stderr)
        return None, False

    fallback_raw_url = (
        f"https://raw.githubusercontent.com/{GITHUB_REPO}/"
        f"{GITHUB_PDF_BRANCH}/{GITHUB_PDF_DIR}/{filename}"
    )

    try:
        with open(local_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")

        api_url = (
            f"https://api.github.com/repos/{GITHUB_REPO}/"
            f"contents/{GITHUB_PDF_DIR}/{filename}"
        )

        payload = json.dumps({
            "message": f"Upload submission PDF: {filename}",
            "content": content_b64,
            "branch": GITHUB_PDF_BRANCH,
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=payload,
            method="PUT",
            headers={
                "Authorization": f"token {github_pat}",
                "Content-Type": "application/json",
                "User-Agent": "TSM2-Submission-Portal",
                "Accept": "application/vnd.github.v3+json",
            },
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            permanent_url = result.get("content", {}).get("download_url") or fallback_raw_url
            print(f"[GITHUB PDF] Uploaded: {permanent_url}", file=sys.stderr)
            return permanent_url, True

    except urllib.error.HTTPError as e:
        if e.code == 422:
            print(f"[GITHUB PDF] File already exists, using existing URL: {fallback_raw_url}", file=sys.stderr)
            return fallback_raw_url, True
        try:
            body = e.read().decode("utf-8", errors="ignore")[:500]
        except Exception:
            body = ""
        print(f"[GITHUB PDF ERROR] HTTP {e.code} for {filename}: {body}", file=sys.stderr)
        return None, False

    except Exception as e:
        print(f"[GITHUB PDF ERROR] Failed to upload {filename}: {e}", file=sys.stderr)
        return None, False


def render_pdf_pages_to_images(pdf_path, max_pages=50, dpi=200):
    """Render each page of a PDF to a PNG image and return as base64 data URIs.

    Returns a dict:
        {
          "images": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}, ...],
          "total_pages": int,
          "rendered_pages": int,
          "truncated": bool,
          "error": Optional[str],
        }
    On failure, returns a dict with empty images and an "error" message.
    """
    if not PYMUPDF_AVAILABLE:
        return {"images": [], "total_pages": 0, "rendered_pages": 0, "truncated": False, "error": "pymupdf unavailable"}
    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        pages_to_render = min(total_pages, max_pages)
        images = []
        for page_num in range(pages_to_render):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            png_bytes = pix.tobytes("png")
            b64 = base64.b64encode(png_bytes).decode("ascii")
            images.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })
        doc.close()
        return {
            "images": images,
            "total_pages": total_pages,
            "rendered_pages": pages_to_render,
            "truncated": total_pages > max_pages,
            "error": None,
        }
    except Exception as e:
        print(f"[PDF RENDER] Failed to render PDF: {e}", file=sys.stderr)
        return {"images": [], "total_pages": 0, "rendered_pages": 0, "truncated": False, "error": str(e)}


STATUS_DISPLAY = {
    "PASS": "✅ Pass",
    "NON_COMPLIANT": "❌ Non-Compliant",
}


def extract_pdf_text(pdf_path, max_chars=60000):
    """Extract text from PDF using pdfplumber.

    Returns (text, truncated, page_count) tuple.
    - text: extracted text content (str) or None on error
    - truncated: bool, True if cut at the character limit
    - page_count: total pages in the PDF (0 on error)
    """
    if not PDFPLUMBER_AVAILABLE:
        print("[PDF EXTRACTION] pdfplumber unavailable; skipping extraction.", file=sys.stderr)
        return None, False, 0
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
                        remaining = max_chars - total_chars
                        text_parts.append(page_text[:remaining])
                        text_parts.append("\n\n[--- PDF TEXT TRUNCATED AT CHARACTER LIMIT ---]")
                        truncated = True
                        break
                    text_parts.append(page_text)
                    total_chars += len(page_text)
        return "\n\n".join(text_parts), truncated, page_count
    except Exception as e:
        print(f"[PDF EXTRACTION ERROR] {e}", file=sys.stderr)
        return None, False, 0


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class RequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/' or path == '' or path == '/index.html':
            file_path = 'index.html'
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, 'File not found')
        else:
            super().do_GET()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/submit':
            try:
                content_type = self.headers.get('Content-Type', '')
                
                if 'multipart/form-data' in content_type:
                    self.handle_multipart_submission()
                else:
                    self.handle_json_submission()
                    
            except Exception as e:
                print(f"Unhandled exception: {type(e).__name__}: {str(e)}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                self.send_json_response(500, {'error': f'Server error: {str(e)}'})
        else:
            self.send_json_response(404, {'error': 'Not found'})
    
    def sanitize_filename(self, filename):
        import re
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:96] + ext
        return filename if filename else 'document.pdf'
    
    def validate_pdf(self, content, filename):
        MAX_FILE_SIZE = 100 * 1024 * 1024
        if len(content) > MAX_FILE_SIZE:
            return False, f'File size exceeds 100MB limit (got {len(content) / 1024 / 1024:.1f}MB)'
        
        if not filename.lower().endswith('.pdf'):
            return False, 'File must be a PDF document (.pdf extension required)'
        
        if len(content) < 4 or content[:4] != b'%PDF':
            return False, 'Invalid PDF file (file does not appear to be a valid PDF)'
        
        return True, None
    
    def handle_multipart_submission(self):
        content_type = self.headers['Content-Type']
        content_length = int(self.headers.get('Content-Length', 0))
        
        body = self.rfile.read(content_length)
        
        boundary = content_type.split('boundary=')[1].encode()
        parts = body.split(b'--' + boundary)
        
        title = ''
        body_text = ''
        pdf_filename = None
        pdf_content = None
        pdf_url = None
        user_info = {}
        form_data = {}
        
        for part in parts:
            if b'Content-Disposition' not in part:
                continue
                
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue
                
            header = part[:header_end].decode('utf-8', errors='ignore')
            content = part[header_end + 4:]
            
            if content.endswith(b'\r\n'):
                content = content[:-2]
            
            if 'name="title"' in header:
                title = content.decode('utf-8', errors='ignore').strip()
            elif 'name="body"' in header:
                body_text = content.decode('utf-8', errors='ignore').strip()
            elif 'name="userInfo"' in header:
                try:
                    user_info = json.loads(content.decode('utf-8', errors='ignore').strip())
                except:
                    pass
            elif 'name="formData"' in header:
                try:
                    form_data = json.loads(content.decode('utf-8', errors='ignore').strip())
                except:
                    pass
            elif 'name="pdf"' in header and 'filename=' in header:
                filename_start = header.find('filename="') + 10
                filename_end = header.find('"', filename_start)
                pdf_filename = header[filename_start:filename_end]
                pdf_content = content
        
        if not pdf_filename or not pdf_content or len(pdf_content) == 0:
            self.send_json_response(400, {'error': 'PDF document is required. Please attach a PDF file.'})
            return
        
        is_valid, error_msg = self.validate_pdf(pdf_content, pdf_filename)
        if not is_valid:
            self.send_json_response(400, {'error': error_msg})
            return
        
        safe_filename = self.sanitize_filename(pdf_filename)
        unique_id = str(uuid.uuid4())[:8]
        final_filename = f"{unique_id}_{safe_filename}"
        pdf_path = os.path.join('uploads', final_filename)
        
        os.makedirs('uploads', exist_ok=True)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
        if domain:
            local_pdf_url = f"https://{domain}/uploads/{final_filename}"
        else:
            local_pdf_url = f"/uploads/{final_filename}"
        pdf_url = local_pdf_url

        print(f"PDF saved: {pdf_path} ({len(pdf_content)} bytes)", file=sys.stderr)
        print(f"Processing submission: {title}", file=sys.stderr)
        
        # Extract PDF text for AI assessment
        pdf_text, pdf_truncated, pdf_page_count = extract_pdf_text(pdf_path)
        pdf_extraction_failed = False
        if pdf_text is None:
            pdf_extraction_failed = True
        elif len(pdf_text.strip()) == 0:
            pdf_text = None
            pdf_extraction_failed = True
            print(f"[PDF EXTRACTION] PDF appears image-based; no extractable text.", file=sys.stderr)
        else:
            print(f"[PDF EXTRACTION] {pdf_page_count} pages, {len(pdf_text)} chars, truncated={pdf_truncated}", file=sys.stderr)

        # Render PDF pages to images for multimodal vision analysis
        render_result = render_pdf_pages_to_images(pdf_path)
        if render_result.get("error"):
            print(f"[PDF RENDER] Vision unavailable: {render_result['error']}", file=sys.stderr)
        else:
            print(f"[PDF RENDER] Rendered {render_result['rendered_pages']}/{render_result['total_pages']} pages at 200 DPI", file=sys.stderr)

        # Upload PDF to GitHub for permanent storage (after extraction + render, before issue creation)
        permanent_pdf_url, pdf_upload_success = upload_pdf_to_github(
            local_path=pdf_path,
            filename=final_filename,
            github_pat=os.environ.get("GITHUB_PAT", ""),
        )
        if pdf_upload_success and permanent_pdf_url:
            pdf_url = permanent_pdf_url
        else:
            print("[GITHUB PDF] Falling back to local Replit URL for PDF link", file=sys.stderr)

        compliance_result = None
        if form_data:
            compliance_result = self.check_compliance_with_grok(
                form_data,
                pdf_text=pdf_text,
                pdf_extraction_failed=pdf_extraction_failed,
                render_result=render_result,
            )

        if pdf_url:
            body_text = body_text.replace(
                f'- **PDF Attached:** {pdf_filename}',
                f'- **PDF Attached:** [{pdf_filename}]({pdf_url})'
            )

            if compliance_result:
                criteria_list = compliance_result.get('criteria', [])
                overall_status = compliance_result.get('overall_status', 'UNAVAILABLE')
                summary = compliance_result.get('message', 'No summary provided.')
                minimum_corrections = compliance_result.get('minimum_corrections', [])
                is_error = compliance_result.get('error', False)

                extraction_note = ""
                if pdf_extraction_failed:
                    extraction_note = "\n> ⚠️ Note: PDF text extraction failed. The AI assessment is based on form-field metadata only, with reduced confidence.\n"
                elif pdf_truncated:
                    extraction_note = f"\n> ⚠️ Note: The PDF text was truncated at approximately 60,000 characters ({pdf_page_count} pages total). The AI assessment is based on the content up to the truncation point.\n"

                if render_result.get("error") or not render_result.get("images"):
                    extraction_note += "\n> ⚠️ **Visual analysis unavailable for this submission.** The PDF could not be rendered to images. The pre-check assessment is based on extracted text only.\n"
                else:
                    rp = render_result['rendered_pages']
                    tp = render_result['total_pages']
                    vis_note = f"\n> 🔬 **Visual analysis:** {rp} of {tp} pages rendered to images at 200 DPI and analyzed alongside extracted text."
                    if render_result.get("truncated"):
                        vis_note += f" Pages beyond page {rp} were not rendered visually but their text was still extracted."
                    extraction_note += vis_note + "\n"

                if is_error or overall_status == "UNAVAILABLE":
                    compliance_section = f"""

---

### AI Structural Pre-Check (9-Criteria Scorecard, PDF-grounded)

> **This is an automated structural screening, not a scientific evaluation.**

**Overall Status:** UNAVAILABLE

The AI pre-check could not be completed. This does not affect the submission — it proceeds to manual review.

**Reason:** {summary}
"""
                elif criteria_list:
                    scorecard_rows = ""
                    for c in criteria_list:
                        rendered_status = STATUS_DISPLAY.get(c.get('status', ''), c.get('status', ''))
                        scorecard_rows += f"| {c.get('id', '')} | {c.get('name', '')} | {rendered_status} | {c.get('reason', '')} |\n"

                    compliance_section = f"""

---

### AI Structural Pre-Check (9-Criteria Scorecard, PDF-grounded)

> **This is an automated structural screening, not a scientific evaluation.**
> The AI pre-check evaluates structure, not scientific truth.
> A submission that contradicts TSM2 can still pass; a submission that agrees with TSM2 can still fail.
> Final compliance determination is made by a qualified examiner.

**Overall Status:** {overall_status}

| # | Criterion | Status | Reason |
| --- | --- | --- | --- |
{scorecard_rows}{extraction_note}
**Summary:** {summary}
"""

                    if overall_status == "NON_COMPLIANT":
                        non_compliant_criteria = [c for c in criteria_list if c.get('status') == 'NON_COMPLIANT']
                        if non_compliant_criteria:
                            corrections_md = ""
                            for c in non_compliant_criteria:
                                correction = c.get('required_correction') or 'No correction provided.'
                                corrections_md += f"\n**{c.get('id', '?')}. {c.get('name', 'Unknown')}**\n\n{correction}\n"
                            compliance_section += f"""
---

### Minimum Corrections Required for Compliance

The following corrections must be addressed for this submission to meet structural compliance. Each criterion below failed; the prescribed correction is shown.
{corrections_md}
Once these corrections are addressed, the submission may be revised and re-submitted for re-evaluation.
"""
                else:
                    compliance_section = f"""

---

### AI Structural Pre-Check (9-Criteria Scorecard, PDF-grounded)

> **This is an automated structural screening, not a scientific evaluation.**

**Overall Status:** {overall_status}
{extraction_note}
**Summary:** {summary}
"""
                body_text += compliance_section
        
        result = self.create_github_issue(title, body_text)
        
        if result.get('success'):
            print(f"User info received (private): {user_info.get('name', 'Unknown')} - {user_info.get('email', 'No email')}", file=sys.stderr)
            
            issue_number = result.get('number')
            issue_url = result.get('html_url')
            
            self.apply_github_labels(issue_number, compliance_result, form_data)
            self.send_examiner_notification(user_info, form_data, title, issue_url, issue_number, compliance_result)
            self.send_submitter_email(user_info, form_data, issue_number, issue_url, compliance_result)
            
            response_data = {
                'success': True,
                'html_url': result.get('html_url'),
                'number': result.get('number')
            }
            if compliance_result:
                frontend_check = {k: v for k, v in compliance_result.items() if k != 'error'}
                response_data['complianceCheck'] = frontend_check
            
            self.send_json_response(200, response_data)
        else:
            self.send_json_response(result.get('code', 500), {'error': result.get('error')})
    
    def handle_json_submission(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        print(f"Received POST request, content length: {content_length}", file=sys.stderr)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}", file=sys.stderr)
            self.send_json_response(400, {'error': 'Invalid JSON in request'})
            return
            
        title = data.get('title', '')
        body = data.get('body', '')
        
        print(f"Parsed request - Title: {title[:50]}...", file=sys.stderr)
        
        result = self.create_github_issue(title, body)
        
        if result.get('success'):
            self.send_json_response(200, {
                'success': True,
                'html_url': result.get('html_url'),
                'number': result.get('number')
            })
        else:
            self.send_json_response(result.get('code', 500), {'error': result.get('error')})
    
    def check_compliance_with_grok(self, form_data, pdf_text=None, pdf_extraction_failed=False, render_result=None):
        grok_api_key = os.environ.get('GROK_API_KEY')
        if not grok_api_key:
            print("GROK_API_KEY not configured, skipping compliance check", file=sys.stderr)
            return {
                "compliant": False,
                "message": "AI pre-check not configured.",
                "overall_status": "UNAVAILABLE",
                "criteria": [],
                "minimum_corrections": [],
                "error": True,
            }

        try:
            submission_title = form_data.get('submission_title', 'Not provided')
            core_claim = form_data.get('core_claim', 'Not provided')
            primary_scale = form_data.get('primary_scale', 'Not provided')
            falsifiability = form_data.get('falsifiability', 'Not provided')

            if pdf_extraction_failed or not pdf_text:
                pdf_section = "[PDF text could not be extracted. Assess based on the metadata fields above only. Note in your summary that the assessment is limited to form fields due to PDF extraction failure.]"
            else:
                pdf_section = pdf_text

            render_result = render_result or {"images": [], "total_pages": 0, "rendered_pages": 0, "truncated": False, "error": "no render"}
            vision_images = render_result.get("images", [])
            vision_truncated = render_result.get("truncated", False)
            vision_total = render_result.get("total_pages", 0)
            vision_rendered = render_result.get("rendered_pages", 0)
            vision_error = render_result.get("error")

            prompt = f"""You are screening a submission to the TSM2 Institute for Cosmology against 9 structural criteria. Evaluate structure, methodology, and epistemic discipline only — do NOT judge scientific merit, correctness, or alignment with any framework.

SUBMISSION METADATA (provided for orientation only — assess from PDF text below, not from these fields):
CRITICAL INSTRUCTION: The metadata fields above (especially the falsifiability condition) are the submitter's SELF-DESCRIPTION of their work. They may be more polished than what the PDF actually contains. Always assess from the PDF text. If the PDF does not contain what the form field claims, score based on what is in the PDF, not what the form field says.
- Title: {submission_title}
- Submitter's stated core claim: {core_claim}
- Submitter's stated primary scale: {primary_scale}
- Submitter's stated falsifiability condition: {falsifiability}

PDF TEXT:
---
{pdf_section}
---

EVALUATE AGAINST THESE 9 CRITERIA, using BINARY status only: PASS or NON_COMPLIANT.

1. CLEAR CORE CLAIM — Is there an identifiable, consistent central proposition? The claim should be stated clearly enough that a reader can identify what the manuscript is asserting. It does not need to be reducible to a single sentence — coherent restatements across the document are acceptable. PASS if a clear central claim is identifiable. NON_COMPLIANT if the claim is incoherent, contradictory across sections, or cannot be extracted.

2. DEFINED TERMS — Are the key technical terms operationally defined and consistently applied? Definitions can be in a glossary, a definitions section, or inline at first use. PASS if the primary technical vocabulary is defined and used consistently. NON_COMPLIANT if core terms are undefined, used inconsistently, or rely on metaphor without operational grounding.

3. MECHANISM — Is there a coherent mechanism pathway that explains how the claim leads to its consequences? The mechanism can be conceptual rather than formally axiomatized — what matters is that a generative sequence exists (e.g., "polarity → distinction → relation → order → number → operations"). PASS if a coherent mechanism pathway is present, even if conceptual. NON_COMPLIANT if no mechanism is offered, or if the paper explicitly disclaims any generative/causal pathway.

4. TEST PATH — Does the manuscript provide at least one explicit testable procedure? Tests can be experimental, computational, mathematical, or observational. Each test must include: (a) a prediction or expected outcome, (b) a procedure for evaluating it, and (c) a condition under which the test would fail. PASS if at least one testable procedure meeting all three elements is present. NON_COMPLIANT if "tests" consist only of compatibility observations, interpretive mappings, or post-hoc pattern matching without a defined failure condition.

5. FALSIFIABILITY — Does the manuscript contain explicit falsifiers — conditions under which the claim or framework would be rejected? Falsifiers should be identifiable failure conditions (e.g., "discovery of a fundamental equation lacking frequency-mode representation"). They do not need to be expressed as binary numerical thresholds. PASS if at least one identifiable falsifier is stated. NON_COMPLIANT if the framework can absorb any contradictory observation through reinterpretation, or no failure conditions are articulated.

6. DEPENDENCY TRANSPARENCY — Does the author explicitly acknowledge assumptions, conceptual scope, limitations, and what the framework does not claim? PASS if a dedicated limitations/scope/assumptions section is present, or if these acknowledgments are clearly distributed and identifiable. NON_COMPLIANT if assumptions are hidden, unstated, or the manuscript overreaches its own scope.

7. NON-ARBITRARY SELECTION — Is the selection of primitives, categories, or analytical units justified? The manuscript should explain why these specific elements were chosen and why alternatives were rejected or considered. PASS if a justification section or argument is present (e.g., a "Why these primitives?" section comparing alternatives). NON_COMPLIANT if selection is post-hoc or unjustified.

8. PREDICTIVE CAPABILITY — Does the manuscript produce at least one measurable prediction, scaling relation, or numerical consequence derived from the framework? Predictions can be quantitative scaling relations, numerical values, observational signatures, or model-specific expected outcomes. PASS if at least one explicit prediction is derivable from the framework. NON_COMPLIANT if the manuscript only re-describes or re-interprets existing data without generating new predictions.

9. REPRODUCIBILITY — Could an independent reviewer reproduce the analysis using the methodology, sources, and procedures described? PASS if the logical framework, cited equations, and procedures are independently traceable. NON_COMPLIANT if the methodology cannot be replicated from the manuscript alone.

For each criterion, return:
- status: either "PASS" or "NON_COMPLIANT" (binary only — no conditional states)
- reason: one short paragraph (1-3 sentences) describing what is present or absent in the PDF that supports this verdict. Cite specific sections, figures, or terms where possible.
- required_correction: ONLY populated when status is NON_COMPLIANT. This must be a PRESCRIPTIVE INSTRUCTION telling the submitter what to add, not a diagnostic description of the gap. Use Geoff's voice:
  - Start with a concrete action: "Add a dedicated section titled X" or "Provide at least one Y" or "Justify the selection of Z by..."
  - Include 2-4 bulleted examples of what the corrected content might look like
  - End with a clear quality bar: "These must include a prediction, procedure, and failure condition" or similar
  - Set required_correction to null when status is PASS

CRITICAL: The required_correction is the submitter's repair instruction. They should be able to action it directly. Do NOT write generic feedback like "consider improving X" — write specific instructions like "Add a section titled 'Potential Falsifiers' listing at least three failure conditions. Examples may include: (a) discovery of foundational equations irreducible to oscillatory representation, (b) proof that polarity cannot generate required mathematical structures, (c) observational signatures incompatible with the framework. Each falsifier must be an identifiable failure condition the framework could not absorb."

Compute one overall verdict:

OVERALL_STATUS:
- "COMPLIANT" if ALL 9 criteria are PASS
- "NON_COMPLIANT" if any criterion is NON_COMPLIANT

Also produce minimum_corrections — an ordered list of the required corrections from the NON_COMPLIANT criteria, in criterion order. This is empty when overall_status is COMPLIANT.

Respond in this exact JSON format only — no markdown, no preamble, no trailing text:

{{
  "criteria": [
    {{"id": 1, "name": "Clear Core Claim", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 2, "name": "Defined Terms", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 3, "name": "Mechanism", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 4, "name": "Test Path", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 5, "name": "Falsifiability", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 6, "name": "Dependency Transparency", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 7, "name": "Non-Arbitrary Selection", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 8, "name": "Predictive Capability", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}},
    {{"id": 9, "name": "Reproducibility", "status": "PASS|NON_COMPLIANT", "reason": "...", "required_correction": "..." or null}}
  ],
  "overall_status": "COMPLIANT|NON_COMPLIANT",
  "minimum_corrections": ["...", "..."],
  "summary": "One short paragraph (2-4 sentences) summarizing the submission's structural standing. If COMPLIANT, state that all 9 criteria are met and note any recommended improvements. If NON_COMPLIANT, state which criteria failed and reference the minimum corrections list."
}}"""

            user_prompt_text = prompt
            if vision_images and vision_truncated:
                truncation_note = (
                    f"NOTE: This PDF has {vision_total} pages. "
                    f"Only the first {vision_rendered} pages have been "
                    f"rendered as images for visual analysis. The text extraction "
                    f"covers the full document."
                )
                user_prompt_text = truncation_note + "\n\n" + user_prompt_text

            if vision_images:
                user_content = list(vision_images)
                user_content.append({"type": "text", "text": user_prompt_text})
                model_name = "grok-4"
            else:
                user_content = user_prompt_text
                model_name = "grok-3-mini"

            request_data = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a structural compliance screener for the TSM2 Institute for Cosmology. Your task is to assess scientific submissions against 9 structural criteria covering claim clarity, mechanism, falsifiability, methodology, predictive capability, and reproducibility. You assess structure and methodological discipline, not scientific truth, and not agreement with any particular theoretical framework. A submission can be excellent structurally while contradicting TSM2, or be aligned with TSM2 while failing structurally. Judge structure only. Respond only with valid JSON in the schema specified."},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.3,
                "max_tokens": 4000,
            }

            req = urllib.request.Request(
                'https://api.x.ai/v1/chat/completions',
                data=json.dumps(request_data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {grok_api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'TSM2-Submission-Portal',
                },
                method='POST',
            )

            start_time = time.time()
            with urllib.request.urlopen(req, timeout=300) as response:
                elapsed = time.time() - start_time
                result = json.loads(response.read().decode('utf-8'))
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                pdf_chars = len(pdf_section) if pdf_section else 0
                print(f"[GROK] Model: {model_name}, Response time: {elapsed:.1f}s, PDF chars: {pdf_chars}, Vision images: {len(vision_images)} (truncated={vision_truncated}, error={vision_error})", file=sys.stderr)

                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                try:
                    ai_result = json.loads(content)
                    print(f"Grok compliance check parsed OK", file=sys.stderr)

                    if "criteria" not in ai_result and "compliant" in ai_result:
                        # Legacy format fallback
                        overall_status = "COMPLIANT" if ai_result["compliant"] else "NON_COMPLIANT"
                        summary = ai_result.get("message", "Legacy format response.")
                        criteria = []
                        minimum_corrections = []
                    else:
                        criteria = ai_result.get("criteria", [])
                        overall_status = ai_result.get("overall_status", "NON_COMPLIANT")
                        summary = ai_result.get("summary", "No summary provided.")
                        minimum_corrections = ai_result.get("minimum_corrections", [])

                    compliant = (overall_status == "COMPLIANT")

                    return {
                        "compliant": compliant,
                        "message": summary,
                        "overall_status": overall_status,
                        "criteria": criteria,
                        "minimum_corrections": minimum_corrections,
                    }
                except (json.JSONDecodeError, KeyError, TypeError):
                    print(f"Could not parse Grok response: {content[:500]}", file=sys.stderr)
                    return {
                        "compliant": False,
                        "message": "AI pre-check returned an unexpected format. Manual review required.",
                        "overall_status": "UNAVAILABLE",
                        "criteria": [],
                        "minimum_corrections": [],
                        "error": True,
                    }

        except urllib.error.HTTPError as e:
            error_msg = e.read().decode()
            print(f"[GROK ERROR] Status: {e.code}, Body: {error_msg[:500]}", file=sys.stderr)
            sys.stderr.flush()
            return {
                "compliant": False,
                "message": f"Grok API error (HTTP {e.code}). Manual review required.",
                "overall_status": "UNAVAILABLE",
                "criteria": [],
                "minimum_corrections": [],
                "error": True,
            }
        except Exception as e:
            print(f"Grok compliance check error: {str(e)}", file=sys.stderr)
            return {
                "compliant": False,
                "message": f"AI pre-check error: {str(e)}. Manual review required.",
                "overall_status": "UNAVAILABLE",
                "criteria": [],
                "minimum_corrections": [],
                "error": True,
            }
    
    def apply_github_labels(self, issue_number, compliance_result, form_data=None):
        import threading

        def _apply():
            github_token = os.environ.get('GITHUB_PAT')
            if not github_token:
                print("Cannot apply labels: GITHUB_PAT not configured", file=sys.stderr)
                return
            
            overall_status = compliance_result.get('overall_status', 'UNAVAILABLE') if compliance_result else 'UNAVAILABLE'

            labels = ["Pending Review"]
            if overall_status == "COMPLIANT":
                labels.append("AI Pre-Check: Compliant")
            elif overall_status == "NON_COMPLIANT":
                labels.append("AI Pre-Check: Non-Compliant")
            else:
                labels.append("Screening: Unavailable")

            primary_scale = (form_data or {}).get("primary_scale", "")
            scale_label = SCALE_LABELS.get(primary_scale)
            if scale_label:
                labels.append(scale_label)
            
            try:
                url = f'https://api.github.com/repos/TSM2Institute/submissions/issues/{issue_number}/labels'
                req = urllib.request.Request(
                    url,
                    data=json.dumps({"labels": labels}).encode('utf-8'),
                    headers={
                        'Authorization': f'token {github_token}',
                        'Accept': 'application/vnd.github.v3+json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'TSM2-Submission-Portal'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    print(f"Labels applied to issue #{issue_number}: {labels}", file=sys.stderr)
            except Exception as e:
                print(f"Failed to apply labels to issue #{issue_number}: {str(e)}", file=sys.stderr)
        
        t = threading.Thread(target=_apply, daemon=True)
        t.start()
    
    def send_examiner_notification(self, user_info, form_data, title, issue_url, issue_number, compliance_result):
        try:
            name = user_info.get('name', 'Not provided')
            email = user_info.get('email', 'Not provided')
            organization = user_info.get('organization', 'Not provided')
            phone = user_info.get('phone', 'Not provided')
            website = user_info.get('website', 'Not provided')

            primary_scale = form_data.get('primary_scale', 'Not specified')
            core_claim = form_data.get('core_claim', 'Not provided')

            overall_status = (compliance_result or {}).get('overall_status', 'UNAVAILABLE')
            summary = (compliance_result or {}).get('message') or (compliance_result or {}).get('summary') or 'No AI summary available.'
            criteria = (compliance_result or {}).get('criteria', []) if compliance_result else []

            failed_section = ""
            if overall_status == "NON_COMPLIANT":
                lines = []
                for c in criteria:
                    if c.get('status') == 'NON_COMPLIANT':
                        cname = c.get('name') or f"Criterion {c.get('id', '?')}"
                        creason = c.get('reason', 'No details')
                        lines.append(f"- {cname}: {creason}")
                if lines:
                    failed_section = "Failed criteria:\n" + "\n".join(lines) + "\n\n"

            email_subject = f"[TSM2-SUB] New Submission: {title} — {overall_status}"

            email_body = f"""New submission received.

SUBMISSION DETAILS
Title: {title}
Primary Scale: {primary_scale}
Core Claim: {core_claim}
GitHub Issue: #{issue_number} — {issue_url}

SUBMITTER DETAILS (PRIVATE)
Name: {name}
Email: {email}
Organization: {organization}
Phone: {phone}
Website: {website}

AI PRE-CHECK RESULT: {overall_status}

{failed_section}Summary: {summary}

View full issue: {issue_url}
"""

            emailutil.send_email_async(
                to_address="info@tsm2.org",
                subject=email_subject,
                body_text=email_body,
            )
        except Exception as e:
            print(f"Examiner email notification error: {str(e)}", file=sys.stderr)
    
    def send_submitter_email(self, user_info, form_data, issue_number, issue_url, compliance_result):
        from datetime import datetime

        try:
            submitter_name = user_info.get('name', 'Submitter')
            submitter_email = user_info.get('email', '')
            if not submitter_email:
                print("No submitter email provided, skipping submitter notification", file=sys.stderr)
                return

            submission_title = form_data.get('submission_title', 'Untitled')
            primary_scale = form_data.get('primary_scale', 'Not specified')
            date_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

            overall_status = (compliance_result or {}).get('overall_status', 'UNAVAILABLE')
            criteria = (compliance_result or {}).get('criteria', []) if compliance_result else []

            reference_block = f"""SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Title: {submission_title}
Primary Scale: {primary_scale}
Date: {date_str}"""

            if overall_status == "COMPLIANT":
                middle_section = f"""{reference_block}

AI STRUCTURAL PRE-CHECK: COMPLIANT
All 9 structural criteria were met.

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission is now pending review by a qualified examiner.
- Structural compliance does not constitute scientific validation or endorsement.
- You will be contacted if any further information is required.

You can view your submission at:
{issue_url}"""

            elif overall_status == "NON_COMPLIANT":
                failed_lines = []
                corrections = []
                for c in criteria:
                    if c.get('status') == 'NON_COMPLIANT':
                        name = c.get('name', f"Criterion {c.get('id', '?')}")
                        reason = c.get('reason', 'No details')
                        correction = c.get('required_correction') or 'See GitHub issue for the full prescribed correction.'
                        failed_lines.append(f"- {name}: {reason}\n  Correction required: {correction}")
                        corrections.append(f"- {correction}")
                failed_text = "\n".join(failed_lines) if failed_lines else "- Details unavailable. See the GitHub issue for the full scorecard."
                corrections_text = "\n".join(corrections) if corrections else "- See the GitHub issue for the full list of corrections."

                middle_section = f"""{reference_block}

AI STRUCTURAL PRE-CHECK: NON-COMPLIANT
The automated screening identified structural gaps in the following criteria:

{failed_text}

MINIMUM CORRECTIONS REQUIRED
{corrections_text}

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission will still proceed to examiner review.
- The corrections listed above are structural requirements, not judgements on scientific merit.
- You may revise and resubmit at any time.

You can view the full assessment at:
{issue_url}"""

            else:
                middle_section = f"""{reference_block}

AI STRUCTURAL PRE-CHECK: UNAVAILABLE
The automated screening could not be completed at this time. This does not affect your submission — it will proceed directly to examiner review.

You can view your submission at:
{issue_url}"""

            email_body = f"""Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

{middle_section}

Thank you for your submission.

TSM2 Institute for Cosmology
info@tsm2.org
"""

            email_subject = f"TSM2 Institute — Submission Received: {submission_title}"

            emailutil.send_email_async(
                to_address=submitter_email,
                subject=email_subject,
                body_text=email_body,
            )
            print(f"[SUBMITTER EMAIL] Queued for {submitter_email} (status={overall_status})", file=sys.stderr)

        except Exception as e:
            print(f"Submitter email error: {str(e)}", file=sys.stderr)
    
    def create_github_issue(self, title, body):
        github_token = os.environ.get('GITHUB_PAT')
        if not github_token:
            print("ERROR: GitHub PAT not configured", file=sys.stderr)
            return {'success': False, 'code': 500, 'error': 'GitHub PAT not configured. Please add GITHUB_PAT to Replit Secrets.'}
        
        repo_owner = 'TSM2Institute'
        repo_name = 'submissions'
        
        issue_data = {
            'title': title,
            'body': body
        }
        
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
        print(f"Making request to: {url}", file=sys.stderr)
        
        req = urllib.request.Request(
            url,
            data=json.dumps(issue_data).encode('utf-8'),
            headers={
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json',
                'User-Agent': 'TSM2-Submission-Portal'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"SUCCESS: Issue created - {result.get('html_url')}", file=sys.stderr)
                return {
                    'success': True,
                    'html_url': result.get('html_url'),
                    'number': result.get('number')
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"GitHub API HTTPError {e.code}: {error_body}", file=sys.stderr)
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get('message', error_body)
            except:
                error_msg = error_body
            return {'success': False, 'code': e.code, 'error': f'GitHub API error: {error_msg}'}
        except urllib.error.URLError as e:
            print(f"Network URLError: {str(e)}", file=sys.stderr)
            return {'success': False, 'code': 500, 'error': f'Network error: {str(e)}'}
    
    def send_json_response(self, code, data):
        try:
            response_body = json.dumps(data).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_body)))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_body)
            self.wfile.flush()
            print(f"Response sent: {code} - {data}", file=sys.stderr)
        except Exception as e:
            print(f"Error sending response: {str(e)}", file=sys.stderr)
    
    def end_headers(self):
        super().end_headers()
    
    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format % args))
        sys.stderr.flush()

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            print(f"Request handling error: {type(e).__name__}: {e}", file=sys.stderr)

if __name__ == '__main__':
    import signal
    
    is_production = os.environ.get('REPLIT_DEPLOYMENT') is not None
    port = 80 if is_production else 5000
    
    print(f'Starting server on port {port}...', file=sys.stderr)
    sys.stderr.flush()
    server = ThreadingHTTPServer(('0.0.0.0', port), RequestHandler)
    
    def handle_shutdown(signum, frame):
        print(f"Received signal {signum}, shutting down...", file=sys.stderr)
        sys.stderr.flush()
        server.shutdown()
    
    def handle_sighup(signum, frame):
        print(f"Received SIGHUP, ignoring...", file=sys.stderr)
        sys.stderr.flush()
    
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGHUP, handle_sighup)
    
    print(f'Server running on port {port}', file=sys.stderr)
    sys.stderr.flush()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Server stopped", file=sys.stderr)
        sys.stderr.flush()
        server.server_close()
