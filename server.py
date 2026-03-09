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
import replitmail


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
            pdf_url = f"https://{domain}/uploads/{final_filename}"
        else:
            pdf_url = f"/uploads/{final_filename}"
        
        print(f"PDF saved: {pdf_path} ({len(pdf_content)} bytes)", file=sys.stderr)
        print(f"Processing submission: {title}", file=sys.stderr)
        
        compliance_result = None
        if form_data:
            compliance_result = self.check_compliance_with_grok(form_data)
        
        if pdf_url:
            body_text = body_text.replace(
                f'- **PDF Attached:** {pdf_filename}',
                f'- **PDF Attached:** [{pdf_filename}]({pdf_url})'
            )
            
            if compliance_result:
                criteria_list = compliance_result.get('criteria', [])
                overall = compliance_result.get('overall', 'NEEDS REVIEW')
                summary = compliance_result.get('message', 'No summary provided.')
                is_error = compliance_result.get('error', False)
                
                if is_error or overall == "UNAVAILABLE":
                    compliance_section = f"""

---

### AI Structural Pre-Check (9-Criteria Scorecard)

> **This is an automated structural screening, not a scientific evaluation.**

**Overall: UNAVAILABLE**

AI pre-check could not be completed. This does not affect the submission — it will proceed to manual review.

**Reason:** {summary}
"""
                elif criteria_list:
                    scorecard_rows = ""
                    for c in criteria_list:
                        scorecard_rows += f"| {c.get('id', '')} | {c.get('name', '')} | {c.get('status', '')} | {c.get('note', '')} |\n"
                    
                    compliance_section = f"""

---

### AI Structural Pre-Check (9-Criteria Scorecard)

> **This is an automated structural screening, not a scientific evaluation.**
> The AI pre-check evaluates structure, not scientific truth.
> Final compliance determination is made by a qualified examiner.

**Overall: {overall}**

| # | Criterion | Status | Note |
|---|-----------|--------|------|
{scorecard_rows}
**Summary:** {summary}
"""
                else:
                    compliance_section = f"""

---

### AI Structural Pre-Check (9-Criteria Scorecard)

> **This is an automated structural screening, not a scientific evaluation.**

**Overall: {overall}**

**Summary:** {summary}
"""
                body_text += compliance_section
        
        result = self.create_github_issue(title, body_text)
        
        if result.get('success'):
            print(f"User info received (private): {user_info.get('name', 'Unknown')} - {user_info.get('email', 'No email')}", file=sys.stderr)
            
            issue_number = result.get('number')
            issue_url = result.get('html_url')
            
            self.apply_github_labels(issue_number, compliance_result)
            self.send_examiner_notification(user_info, title, issue_url, issue_number)
            self.send_submitter_email(user_info, form_data, issue_number, compliance_result)
            
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
    
    def check_compliance_with_grok(self, form_data):
        grok_api_key = os.environ.get('GROK_API_KEY')
        if not grok_api_key:
            print("GROK_API_KEY not configured, skipping compliance check", file=sys.stderr)
            return {
                "compliant": False,
                "message": "AI pre-check not configured.",
                "overall": "UNAVAILABLE",
                "criteria": [],
                "error": True
            }
        
        try:
            submission_title = form_data.get('submission_title', 'Not provided')
            core_claim = form_data.get('core_claim', 'Not provided')
            primary_scale = form_data.get('primary_scale', 'Not provided')
            falsifiability = form_data.get('falsifiability', 'Not provided')
            criteria_definitions = form_data.get('criteria_definitions', False)
            criteria_assumptions = form_data.get('criteria_assumptions', False)
            criteria_mechanism = form_data.get('criteria_mechanism', False)
            criteria_energy = form_data.get('criteria_energy', False)
            criteria_empirical = form_data.get('criteria_empirical', False)
            criteria_category = form_data.get('criteria_category', False)

            prompt = f"""You are screening a submission to the TSM2 Institute for Cosmology against 9 structural criteria. Evaluate structure and completeness only — do NOT judge scientific merit or correctness.

SUBMISSION DATA:
- Title: {submission_title}
- Core Claim: {core_claim}
- Primary Scale: {primary_scale}
- Falsifiability Condition: {falsifiability}

SUBMITTER SELF-CERTIFICATION:
The submitter has confirmed their PDF addresses the following (these are declarations, not content you can verify — note them as "Declared by submitter"):
- Key terms defined: {criteria_definitions}
- Assumptions declared: {criteria_assumptions}
- Mechanism described: {criteria_mechanism}
- Energy conservation addressed: {criteria_energy}
- Empirical anchor identified: {criteria_empirical}
- Category integrity maintained: {criteria_category}

EVALUATE AGAINST THESE 9 CRITERIA:

1. EXPLICIT CLAIM — Is the core claim singular, clear, and non-compound? (Assess from the Core Claim field)
2. KEY TERM DEFINITIONS — Has the submitter declared their PDF defines key terms? (Check self-certification)
3. DECLARED ASSUMPTIONS — Has the submitter declared their PDF states assumptions? (Check self-certification)
4. STATED MECHANISM — Has the submitter declared their PDF describes a causal mechanism? (Check self-certification)
5. ENERGY CONSERVATION — Has the submitter declared their PDF addresses conservation laws? (Check self-certification)
6. EMPIRICAL ANCHOR — Has the submitter declared their PDF identifies observational grounding? (Check self-certification)
7. FALSIFIABILITY — Is the falsifiability condition testable and specific? (Assess from the Falsifiability field)
8. SCALE CONSISTENCY — Is a physical or cosmological scale stated? Does the claim appear consistent with that scale? (Assess from Primary Scale and Core Claim fields)
9. CATEGORY INTEGRITY — Does the core claim use physical causation rather than metaphor or undefined abstraction? (Assess from the Core Claim field)

For criteria 2-6: If the submitter has self-certified (true), mark as "DECLARED" with a note. If false, mark as "MISSING".
For criteria 1, 7, 8, 9: Assess the actual content provided in the form fields.

Respond in this exact JSON format only — no markdown, no preamble:
{{"criteria": [{{"id": 1, "name": "Explicit Claim", "status": "PASS|FLAG|MISSING", "note": "Brief explanation"}}, {{"id": 2, "name": "Key Term Definitions", "status": "DECLARED|MISSING", "note": "Brief explanation"}}, {{"id": 3, "name": "Declared Assumptions", "status": "DECLARED|MISSING", "note": "Brief explanation"}}, {{"id": 4, "name": "Stated Mechanism", "status": "DECLARED|MISSING", "note": "Brief explanation"}}, {{"id": 5, "name": "Energy Conservation", "status": "DECLARED|MISSING", "note": "Brief explanation"}}, {{"id": 6, "name": "Empirical Anchor", "status": "DECLARED|MISSING", "note": "Brief explanation"}}, {{"id": 7, "name": "Falsifiability", "status": "PASS|FLAG", "note": "Brief explanation"}}, {{"id": 8, "name": "Scale Consistency", "status": "PASS|FLAG", "note": "Brief explanation"}}, {{"id": 9, "name": "Category Integrity", "status": "PASS|FLAG", "note": "Brief explanation"}}], "overall": "PASSED|NEEDS REVIEW", "summary": "One sentence overall assessment"}}

Status values:
- PASS = criterion clearly met based on assessed content
- DECLARED = submitter self-certified their PDF addresses this (cannot be verified from form data alone)
- FLAG = potential issue identified — examiner should check
- MISSING = not addressed or not certified

Overall result:
- PASSED = all criteria are PASS or DECLARED, no FLAGS or MISSING
- NEEDS REVIEW = one or more criteria are FLAG or MISSING"""

            request_data = {
                "model": "grok-3-mini",
                "messages": [
                    {"role": "system", "content": "You are a structural compliance screener for the TSM2 Institute for Cosmology. You evaluate whether submissions meet 9 defined structural criteria. You assess structure and completeness, not scientific truth. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            req = urllib.request.Request(
                'https://api.x.ai/v1/chat/completions',
                data=json.dumps(request_data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {grok_api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'TSM2-Submission-Portal'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
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
                    print(f"Grok compliance check: {ai_result}", file=sys.stderr)
                    
                    if "criteria" not in ai_result and "compliant" in ai_result:
                        overall = "PASSED" if ai_result["compliant"] else "NEEDS REVIEW"
                        summary = ai_result.get("message", "Legacy format response.")
                        criteria = []
                        compliant = ai_result["compliant"]
                    else:
                        criteria = ai_result.get("criteria", [])
                        overall = ai_result.get("overall", "NEEDS REVIEW")
                        summary = ai_result.get("summary", "No summary provided.")
                        compliant = (overall == "PASSED")
                    
                    return {
                        "compliant": compliant,
                        "message": summary,
                        "overall": overall,
                        "criteria": criteria
                    }
                except json.JSONDecodeError:
                    print(f"Could not parse Grok response: {content}", file=sys.stderr)
                    return {
                        "compliant": False,
                        "message": "AI pre-check returned an unexpected format. Manual review required.",
                        "overall": "NEEDS REVIEW",
                        "criteria": []
                    }
                    
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode()
            print(f"[GROK ERROR] Status: {e.code}, Body: {error_msg[:500]}", file=sys.stderr)
            sys.stderr.flush()
            return {
                "compliant": False,
                "message": f"Grok API error (HTTP {e.code}). Manual review required.",
                "overall": "UNAVAILABLE",
                "criteria": [],
                "error": True
            }
        except Exception as e:
            print(f"Grok compliance check error: {str(e)}", file=sys.stderr)
            return {
                "compliant": False,
                "message": f"AI pre-check error: {str(e)}. Manual review required.",
                "overall": "UNAVAILABLE",
                "criteria": [],
                "error": True
            }
    
    def apply_github_labels(self, issue_number, compliance_result):
        import threading
        
        def _apply():
            github_token = os.environ.get('GITHUB_PAT')
            if not github_token:
                print("Cannot apply labels: GITHUB_PAT not configured", file=sys.stderr)
                return
            
            overall = compliance_result.get('overall', 'UNAVAILABLE') if compliance_result else 'UNAVAILABLE'
            
            labels = ["Pending Review"]
            if overall == "PASSED":
                labels.append("Screening: Passed")
            elif overall == "NEEDS REVIEW":
                labels.append("Screening: Needs Review")
            else:
                labels.append("Screening: Unavailable")
            
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
    
    def send_examiner_notification(self, user_info, title, issue_url, issue_number):
        import threading
        
        def _send():
            try:
                name = user_info.get('name', 'Not provided')
                email = user_info.get('email', 'Not provided')
                organization = user_info.get('organization', 'Not provided')
                
                email_subject = f"TSM2 Submission #{issue_number}: {title}"
                
                email_body = f"""New TSM2 Submission Received

Submitter Details (Private):
- Name: {name}
- Email: {email}
- Organization: {organization}

Submission:
- Title: {title}
- Issue #: {issue_number}
- GitHub URL: {issue_url}

This information was kept private and is not visible on the public GitHub issue."""
                
                result = replitmail.send_email(email_subject, text=email_body)
                
                if result.get('success'):
                    print(f"Examiner email notification sent successfully", file=sys.stderr)
                else:
                    print(f"Examiner email notification failed: {result.get('error')}", file=sys.stderr)
                    
            except Exception as e:
                print(f"Examiner email notification error: {str(e)}", file=sys.stderr)
        
        t = threading.Thread(target=_send, daemon=True)
        t.start()
    
    def send_submitter_email(self, user_info, form_data, issue_number, compliance_result):
        import threading
        from datetime import datetime
        
        def _send():
            try:
                submitter_name = user_info.get('name', 'Submitter')
                submitter_email = user_info.get('email', '')
                if not submitter_email:
                    print("No submitter email provided, skipping submitter notification", file=sys.stderr)
                    return
                
                submission_title = form_data.get('submission_title', 'Untitled')
                primary_scale = form_data.get('primary_scale', 'Not specified')
                date_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
                
                overall = compliance_result.get('overall', 'UNAVAILABLE') if compliance_result else 'UNAVAILABLE'
                criteria = compliance_result.get('criteria', []) if compliance_result else []
                
                if overall == "PASSED":
                    screening_section = """AI STRUCTURAL PRE-CHECK: PASSED
All 9 structural criteria were addressed."""
                elif overall == "NEEDS REVIEW":
                    flagged_items = ""
                    for c in criteria:
                        status = c.get('status', '')
                        if status in ('FLAG', 'MISSING'):
                            flagged_items += f"- Criterion {c.get('id', '?')} ({c.get('name', 'Unknown')}): {status} - {c.get('note', 'No details')}\n"
                    if not flagged_items:
                        flagged_items = "- Details unavailable\n"
                    screening_section = f"""AI STRUCTURAL PRE-CHECK: NEEDS REVIEW
The automated screening identified potential structural gaps:

{flagged_items.rstrip()}"""
                else:
                    screening_section = """AI STRUCTURAL PRE-CHECK: UNAVAILABLE
The automated screening could not be completed at this time. This does not affect your submission - it will proceed directly to examiner review."""
                
                email_body = f"""Dear {submitter_name},

Your submission "{submission_title}" has been received by the TSM2 Institute for Cosmology.

SUBMISSION REFERENCE
GitHub Issue: #{issue_number}
Submitted: {date_str}
Primary Scale: {primary_scale}

{screening_section}

Please note:
- This is an automated structural screening, not a scientific evaluation.
- Your submission is now pending review by a qualified examiner.
- Structural compliance does not constitute scientific validation or endorsement.
- You will be contacted if any further information is required.

Thank you for your submission.

TSM2 Institute for Cosmology"""
                
                email_subject = f"TSM2 Institute — Submission Received [TSM2-SUB] {submission_title}"
                
                # TODO: Submitter email requires an external email service (e.g., SendGrid, Mailgun, or SMTP).
                # Replit Mail only sends to the verified Replit account owner, not to arbitrary external addresses.
                # The email content is logged here for audit purposes until an external service is integrated.
                print(f"[SUBMITTER EMAIL] Would send to: {submitter_email}", file=sys.stderr)
                print(f"[SUBMITTER EMAIL] Subject: {email_subject}", file=sys.stderr)
                print(f"[SUBMITTER EMAIL] Screening result: {overall}", file=sys.stderr)
                sys.stderr.flush()
                    
            except Exception as e:
                print(f"Submitter email error: {str(e)}", file=sys.stderr)
        
        t = threading.Thread(target=_send, daemon=True)
        t.start()
    
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
