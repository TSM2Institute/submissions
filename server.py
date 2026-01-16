from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import sys

class RequestHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/submit':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                print(f"Received POST request, content length: {content_length}", file=sys.stderr)
                
                data = json.loads(post_data.decode('utf-8'))
                title = data.get('title', '')
                body = data.get('body', '')
                
                print(f"Parsed request - Title: {title[:50]}...", file=sys.stderr)
                
                github_token = os.environ.get('GITHUB_PAT')
                if not github_token:
                    print("ERROR: GitHub PAT not configured", file=sys.stderr)
                    self.send_json_response(500, {'error': 'GitHub PAT not configured. Please add GITHUB_PAT to Replit Secrets.'})
                    return
                
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
                        self.send_json_response(200, {
                            'success': True,
                            'html_url': result.get('html_url'),
                            'number': result.get('number')
                        })
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode('utf-8')
                    print(f"GitHub API HTTPError {e.code}: {error_body}", file=sys.stderr)
                    try:
                        error_json = json.loads(error_body)
                        error_msg = error_json.get('message', error_body)
                    except:
                        error_msg = error_body
                    self.send_json_response(e.code, {'error': f'GitHub API error: {error_msg}'})
                except urllib.error.URLError as e:
                    print(f"Network URLError: {str(e)}", file=sys.stderr)
                    self.send_json_response(500, {'error': f'Network error: {str(e)}'})
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}", file=sys.stderr)
                self.send_json_response(400, {'error': 'Invalid JSON in request'})
            except Exception as e:
                print(f"Unhandled exception: {type(e).__name__}: {str(e)}", file=sys.stderr)
                self.send_json_response(500, {'error': f'Server error: {str(e)}'})
        else:
            self.send_json_response(404, {'error': 'Not found'})
    
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
    # Use port 80 for production deployments, 5000 for development
    is_production = os.environ.get('REPLIT_DEPLOYMENT') is not None
    port = 80 if is_production else 5000
    print(f'Starting server on port {port}...', file=sys.stderr)
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    print(f'Server running on port {port}', file=sys.stderr)
    server.serve_forever()
