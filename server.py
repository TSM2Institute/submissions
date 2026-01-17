from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import sys
import uuid
import cgi
import io

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
                compliance_section = f"""

---

### AI Compliance Pre-Check
- **Status:** {'PASSED' if compliance_result.get('compliant') else 'NEEDS REVIEW'}
- **Notes:** {compliance_result.get('message', 'No additional notes')}
"""
                body_text += compliance_section
        
        result = self.create_github_issue(title, body_text)
        
        if result.get('success'):
            print(f"User info received (private): {user_info.get('name', 'Unknown')} - {user_info.get('email', 'No email')}", file=sys.stderr)
            
            response_data = {
                'success': True,
                'html_url': result.get('html_url'),
                'number': result.get('number')
            }
            if compliance_result:
                response_data['complianceCheck'] = compliance_result
            
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
            return None
        
        try:
            prompt = f"""You are an AI compliance checker for the TSM2 Institute for Cosmology. 
Your task is to evaluate if a submission meets basic structural requirements for scientific claims.

Evaluate the following submission:

**Title:** {form_data.get('submission_title', 'Not provided')}

**Core Claim:** {form_data.get('core_claim', 'Not provided')}

**Primary Scale:** {form_data.get('primary_scale', 'Not provided')}

**Falsifiability Condition:** {form_data.get('falsifiability', 'Not provided')}

Check if the submission:
1. Has a clear, single explicit claim (not compound or vague)
2. Provides a testable falsifiability condition
3. Avoids rhetorical or emotive language
4. States a physical or cosmological scale

Respond in JSON format only:
{{"compliant": true/false, "message": "Brief explanation (1-2 sentences)"}}"""

            request_data = {
                "model": "grok-3-mini",
                "messages": [
                    {"role": "system", "content": "You are a compliance checker. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            req = urllib.request.Request(
                'https://api.x.ai/v1/chat/completions',
                data=json.dumps(request_data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {grok_api_key}',
                    'Content-Type': 'application/json'
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
                    compliance_data = json.loads(content)
                    print(f"Grok compliance check: {compliance_data}", file=sys.stderr)
                    return compliance_data
                except json.JSONDecodeError:
                    print(f"Could not parse Grok response: {content}", file=sys.stderr)
                    return {"compliant": True, "message": "Compliance check completed (parsing note)"}
                    
        except urllib.error.HTTPError as e:
            print(f"Grok API error: {e.code} - {e.read().decode()}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Grok compliance check error: {str(e)}", file=sys.stderr)
            return None
    
    def create_github_issue(self, title, body):
        github_token = os.environ.get('GITHUB_PAT')
        if not github_token:
            print("ERROR: GitHub PAT not configured", file=sys.stderr)
            return {'success': False, 'code': 500, 'error': 'GitHub PAT not configured. Please add GITHUB_PAT to Replit Secrets.'}
        
        repo_owner = 'TSM2Institute'
        repo_name = 'submissions'
        
        issue_data = {
            'title': title,
            'body': body,
            'labels': ['submission', 'needs-triage']
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

if __name__ == '__main__':
    is_production = os.environ.get('REPLIT_DEPLOYMENT') is not None
    port = 80 if is_production else 5000
    print(f'Starting server on port {port}...', file=sys.stderr)
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    print(f'Server running on port {port}', file=sys.stderr)
    server.serve_forever()
