from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5002402843"))

TG_API = f"https://api.telegram.org/bot{TOKEN}"


def tg_send(chat_id, text):
    try:
        requests.post(f"{TG_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def flat_params(raw: dict) -> dict:
    return {k: (v[0] if isinstance(v, list) and v else v) for k, v in raw.items()}


def build_message(data: dict) -> str:
    phone    = data.get("phone") or data.get("number") or ""
    code     = data.get("code") or data.get("sms") or data.get("text") or ""
    service  = data.get("service") or ""
    order_id = data.get("id") or data.get("order_id") or ""

    msg = "📩 *SMS Received*\n━━━━━━━━━━━━━━━━\n"
    if service:
        msg += f"🛍 Service: *{service}*\n"
    if order_id:
        msg += f"🆔 Order ID: `{order_id}`\n"
    if phone:
        msg += f"📞 Phone: `{phone}`\n"
    if code:
        msg += f"🔐 Code: *{code}*\n"
    msg += "━━━━━━━━━━━━━━━━"

    if not phone and not code:
        msg += f"\n📦 Raw: `{json.dumps(data)}`"

    return msg


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        params = flat_params(parse_qs(parsed.query))
        print(f"[SMS GET] {params}")
        msg = build_message(params)
        tg_send(ADMIN_ID, msg)
        self._ok()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")

        try:
            if "application/json" in content_type:
                params = json.loads(body)
            else:
                params = flat_params(parse_qs(body.decode("utf-8")))
        except Exception:
            params = {}

        print(f"[SMS POST] {params}")
        msg = build_message(params)
        tg_send(ADMIN_ID, msg)
        self._ok()

    def _ok(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def log_message(self, format, *args):
        pass
