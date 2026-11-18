"""Tiny stand-in for the DittoFS control-plane API, for demo purposes only.
Response shapes copied from the Go handlers (ShareResponse, ClientRecord). Data is made up.
Usage: python mock_dittofs.py [port]   (requires header 'Authorization: Bearer demo-token' on /api/v1)"""
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

SHARES = [
    {"id": "s1", "name": "/projects", "enabled": True, "read_only": False, "default_permission": "none",
     "quota_bytes": "500 GiB", "used_bytes": 412_000_000_000, "physical_bytes": 301_000_000_000, "usage_percent": 76.8},
    {"id": "s2", "name": "/archive", "enabled": True, "read_only": True, "default_permission": "read",
     "quota_bytes": "", "used_bytes": 91_000_000_000, "physical_bytes": 64_000_000_000, "usage_percent": 0},
]
CLIENTS = [
    {"client_id": "c-1", "protocol": "nfs", "address": "10.0.0.12:871", "connected_at": "2026-11-18T08:01:00Z", "last_activity": "2026-11-18T09:40:10Z", "nfs": {"version": "4.1"}},
    {"client_id": "c-2", "protocol": "smb", "address": "10.0.0.31:50422", "connected_at": "2026-11-18T08:15:00Z", "last_activity": "2026-11-18T09:41:02Z", "smb": {"session_id": 77}},
]
ROUTES = {
    "/health": {"status": "ok"},
    "/health/ready": {"status": "ready", "database": "reachable"},
    "/api/v1/shares": SHARES,
    "/api/v1/adapters": [{"type": "nfs", "enabled": True, "running": True, "port": 12049, "status": {"status": "healthy"}},
                         {"type": "smb", "enabled": True, "running": True, "port": 12445, "status": {"status": "healthy"}}],
    "/api/v1/store/block": [{"name": "local-fs", "kind": "fs"}, {"name": "s3-remote", "kind": "s3"}],
    "/api/v1/blockstore/stats": {"cache_bytes": 12_000_000_000, "remote_bytes": 355_000_000_000},
}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path.startswith("/api/v1") and self.headers.get("Authorization") != "Bearer demo-token":
            return self._send(401, {"error": "unauthorized"})
        body = ROUTES.get(path)
        if path == "/api/v1/clients":
            body = [c for c in CLIENTS if f"protocol={c['protocol']}" in query or "protocol=" not in query]
        elif path.startswith("/api/v1/shares/") and path.endswith("/status"):
            name = "/" + path.split("/")[4]
            if name not in [s["name"] for s in SHARES]:
                return self._send(404, {"error": "Share not found"})
            body = {"status": "healthy", "checked_at": "2026-11-18T09:42:00Z", "offline": {"can_serve_reads": True}}
        if body is None:
            return self._send(404, {"error": "not found"})
        self._send(200, body)
    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, *a): pass

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8080), H).serve_forever()
