import subprocess
import json
import os
import urllib.request
import urllib.error

def get_auth_token():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    if not hostname:
        raise Exception("REPLIT_CONNECTORS_HOSTNAME not found")
    
    result = subprocess.run(
        ["replit", "identity", "create", "--audience", f"https://{hostname}"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to get auth token: {result.stderr}")
    
    token = result.stdout.strip()
    if not token:
        raise Exception("Replit Identity Token not found")
    
    return token, hostname

def send_email(subject, text=None, html=None, attachments=None):
    try:
        auth_token, hostname = get_auth_token()
        
        payload = {"subject": subject}
        if text:
            payload["text"] = text
        if html:
            payload["html"] = html
        if attachments:
            payload["attachments"] = attachments
        
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            f"https://{hostname}/api/v2/mailer/send",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Replit-Authentication": f"Bearer {auth_token}"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {"success": True, "result": result}
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
