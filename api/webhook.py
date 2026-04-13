from http.server import BaseHTTPRequestHandler
import json
import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_KEY = os.environ.get("SMSX_API_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5002402843"))

SMSX_BASE = "https://www.sms-x.org/stubs/handler_api.php"
TG_API = f"https://api.telegram.org/bot{TOKEN}"


def tg_send(chat_id, text, parse_mode="Markdown"):
    requests.post(f"{TG_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }, timeout=10)


def get_balance():
    try:
        resp = requests.get(SMSX_BASE, params={
            "api_key": API_KEY,
            "action": "getBalance"
        }, timeout=10)
        text = resp.text.strip()
        if text.startswith("ACCESS_BALANCE:"):
            return text.split(":")[1]
        return None
    except Exception:
        return None


def handle_command(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user = message.get("from", {})
    name = user.get("first_name", "User")

    if text.startswith("/start"):
        balance = get_balance()
        domain = os.environ.get("VERCEL_URL", "your-domain.vercel.app")
        webhook_url = f"https://{domain}/api/sms"
        if balance:
            msg = (
                f"👤 *Account Info*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🙋 Name: *{name}*\n"
                f"🔑 API Key: `{API_KEY}`\n"
                f"💰 Balance: *${balance}*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📡 SMS Webhook URL:\n`{webhook_url}`\n\n"
                f"_Set this URL in sms-x.org settings._"
            )
        else:
            msg = (
                f"👤 *Account Info*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🙋 Name: *{name}*\n"
                f"🔑 API Key: `{API_KEY}`\n"
                f"⚠️ Could not fetch balance\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📡 SMS Webhook URL:\n`{webhook_url}`\n\n"
                f"_Set this URL in sms-x.org settings._"
            )
        tg_send(chat_id, msg)

    elif text.startswith("/balance") or text.startswith("/account"):
        balance = get_balance()
        if balance:
            tg_send(chat_id, f"💰 Balance: *${balance}*")
        else:
            tg_send(chat_id, "⚠️ Cannot fetch balance. Check your API key.")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            if "message" in update:
                handle_command(update["message"])
        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "Telegram webhook active"}).encode())

    def log_message(self, format, *args):
        pass
