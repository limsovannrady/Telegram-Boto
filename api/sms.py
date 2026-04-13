from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5002402843"))

TG_API = f"https://api.telegram.org/bot{TOKEN}"


def tg_send(chat_id, text, parse_mode="Markdown"):
    requests.post(f"{TG_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }, timeout=10)


def build_sms_message(data: dict) -> str:
    phone = data.get("phone", data.get("number", [""]))[0] if isinstance(data.get("phone", data.get("number")), list) else data.get("phone", data.get("number", ""))
    code = data.get("code", data.get("sms", data.get("text", [""]))[0] if isinstance(data.get("code", data.get("sms", data.get("text"))), list) else data.get("code", data.get("sms", data.get("text", ""))))
    service = (data.get("service", [""])[0] if isinstance(data.get("service"), list) else data.get("service", ""))
    order_id = (data.get("id", data.get("order_id", [""]))[0] if isinstance(data.get("id", data.get("order_id")), list) else data.get("id", data.get("order_id", "")))

    msg = "📩 *SMS Received*\n━━━━━━━━━━━━━━━━\n"
    if service:
        msg += f"🛍️ Service: *{service}*\n"
    if order_id:
        msg += f"🆔 Order ID: `{order_id}`\n"
    if phone:
        msg += f"📞 Phone: `{phone}`\n"
    if code:
        msg += f"🔐 Code / SMS: *{code}*\n"
    msg += "━━━━━━━━━━━━━━━━"

    if not phone and not code:
        clean = {k: (v[0] if isinstance(v, list) else v) for k, v in data.items()}
        msg += f"\n📦 Raw: `{json.dumps(clean)}`"

    return msg


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        msg = build_sms_message(params)
        tg_send(ADMIN_ID, msg)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = json.loads(body)
                flat = {k: v for k, v in data.items()}
            else:
                from urllib.parse import parse_qs
                parsed_body = parse_qs(body.decode("utf-8"))
                flat = {k: (v[0] if isinstance(v, list) else v) for k, v in parsed_body.items()}

            msg = build_sms_message({k: [v] if not isinstance(v, list) else v for k, v in flat.items()})
            tg_send(ADMIN_ID, msg)
        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def log_message(self, format, *args):
        pass
