import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APIFY_API = "https://api.apify.com/v2"
ACTOR_ID = os.environ.get("APIFY_ACTOR_ID", "QJX8h1Odtl2o8RdVq")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
CONTROL_API_KEY = os.environ.get("CONTROL_API_KEY", "")
PORT = int(os.environ.get("PORT", "8080"))
MAX_BODY_BYTES = 25 * 1024 * 1024


def _apify(path, method="GET", body=None, content_type="application/json"):
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN is not configured")
    data = None
    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "User-Agent": "CatalogFix-Control/1.0",
    }
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = content_type
        elif isinstance(body, bytes):
            data = body
            headers["Content-Type"] = content_type
        else:
            data = str(body).encode("utf-8")
            headers["Content-Type"] = content_type
    req = urllib.request.Request(APIFY_API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
            ctype = resp.headers.get("content-type", "")
            if "application/json" in ctype:
                return resp.status, json.loads(raw.decode("utf-8") or "{}"), ctype
            return resp.status, raw, ctype
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        ctype = exc.headers.get("content-type", "")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {"error": raw.decode("utf-8", "replace")[:4000]}
        return exc.code, payload, ctype


def _safe_run_id(value):
    return value if re.fullmatch(r"[A-Za-z0-9_-]{8,80}", value or "") else None


class Handler(BaseHTTPRequestHandler):
    server_version = "CatalogFixControl/1.0"

    def log_message(self, fmt, *args):
        # Do not log Authorization headers or secrets.
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def _json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _bytes(self, status, payload, ctype="application/octet-stream"):
        self.send_response(status)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self):
        if not CONTROL_API_KEY:
            self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "CONTROL_API_KEY is not configured"})
            return False
        expected = f"Bearer {CONTROL_API_KEY}"
        if self.headers.get("Authorization", "") != expected:
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return False
        return True

    def _body_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self._json(200, {
                "ok": True,
                "service": "catalogfix-apify-control",
                "actorId": ACTOR_ID,
                "apifyTokenConfigured": bool(APIFY_TOKEN),
                "controlKeyConfigured": bool(CONTROL_API_KEY),
            })

        if not self._authorized():
            return

        if path == "/v1/status":
            code, data, _ = _apify(f"/acts/{ACTOR_ID}")
            return self._json(code, data)

        if path == "/v1/runs":
            query = ("?" + parsed.query) if parsed.query else "?limit=20&desc=1"
            code, data, _ = _apify(f"/acts/{ACTOR_ID}/runs{query}")
            return self._json(code, data)

        m = re.fullmatch(r"/v1/runs/([^/]+)", path)
        if m:
            run_id = _safe_run_id(m.group(1))
            if not run_id:
                return self._json(400, {"error": "invalid run id"})
            code, data, _ = _apify(f"/actor-runs/{run_id}")
            return self._json(code, data)

        m = re.fullmatch(r"/v1/runs/([^/]+)/logs", path)
        if m:
            run_id = _safe_run_id(m.group(1))
            if not run_id:
                return self._json(400, {"error": "invalid run id"})
            code, data, ctype = _apify(f"/logs/{run_id}")
            if isinstance(data, bytes):
                return self._bytes(code, data, ctype or "text/plain; charset=utf-8")
            return self._json(code, data)

        m = re.fullmatch(r"/v1/runs/([^/]+)/summary", path)
        if m:
            run_id = _safe_run_id(m.group(1))
            if not run_id:
                return self._json(400, {"error": "invalid run id"})
            code, run, _ = _apify(f"/actor-runs/{run_id}")
            if code != 200:
                return self._json(code, run)
            kv_id = (run.get("data") or {}).get("defaultKeyValueStoreId")
            if not kv_id:
                return self._json(404, {"error": "run has no default key-value store"})
            code, data, ctype = _apify(f"/key-value-stores/{kv_id}/records/SUMMARY.json")
            if isinstance(data, bytes):
                return self._bytes(code, data, ctype or "application/json")
            return self._json(code, data)

        return self._json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if not self._authorized():
            return

        if path == "/v1/build":
            payload = self._body_json()
            version = str(payload.get("version") or "1.9")
            tag = str(payload.get("tag") or "latest")
            use_cache = "1" if payload.get("useCache", True) else "0"
            query = urllib.parse.urlencode({
                "version": version,
                "tag": tag,
                "useCache": use_cache,
                "waitForFinish": 0,
            })
            code, data, _ = _apify(f"/acts/{ACTOR_ID}/builds?{query}", method="POST", body={})
            return self._json(code, data)

        if path == "/v1/run":
            payload = self._body_json()
            actor_input = payload.get("input", payload)
            opts = {}
            if "memory" in payload:
                opts["memory"] = int(payload["memory"])
            if "timeout" in payload:
                opts["timeout"] = int(payload["timeout"])
            if "build" in payload:
                opts["build"] = str(payload["build"])
            suffix = ("?" + urllib.parse.urlencode(opts)) if opts else ""
            code, data, _ = _apify(f"/acts/{ACTOR_ID}/runs{suffix}", method="POST", body=actor_input)
            return self._json(code, data)

        m = re.fullmatch(r"/v1/runs/([^/]+)/abort", path)
        if m:
            run_id = _safe_run_id(m.group(1))
            if not run_id:
                return self._json(400, {"error": "invalid run id"})
            code, data, _ = _apify(f"/actor-runs/{run_id}/abort", method="POST", body={})
            return self._json(code, data)

        return self._json(404, {"error": "not found"})


if __name__ == "__main__":
    if not APIFY_TOKEN:
        raise SystemExit("APIFY_TOKEN is required")
    if not CONTROL_API_KEY:
        raise SystemExit("CONTROL_API_KEY is required")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"CatalogFix Apify control listening on :{PORT} for actor {ACTOR_ID}", flush=True)
    server.serve_forever()
