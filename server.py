from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class RequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                title = data.get('title', '')
                body = data.get('body', '')
                
                github_token = os.environ.get('GITHUB_PAT')
                if not github_token:
                    self.send_error_response(500, 'GitHub PAT not configured')
                    return
                
                repo_owner = 'TSM2Institute'
                repo_name = 'submissions'
                
                issue_data = {
                    'title': title,
                    'body': body,
                    'labels': ['submission', 'needs-triage']
                }
                
                url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
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
                    with urllib.request.urlopen(req) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'success': True,
                            'html_url': result.get('html_url'),
                            'number': result.get('number')
                        }).encode('utf-8'))
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode('utf-8')
                    self.send_error_response(e.code, f'GitHub API error: {error_body}')
                except urllib.error.URLError as e:
                    self.send_error_response(500, f'Network error: {str(e)}')
                    
            except json.JSONDecodeError:
                self.send_error_response(400, 'Invalid JSON')
            except Exception as e:
                self.send_error_response(500, str(e))
        else:
            self.send_error_response(404, 'Not found')
    
    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

if __name__ == '__main__':
    port = 5000
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    print(f'Server running on port {port}')
    server.serve_forever()
