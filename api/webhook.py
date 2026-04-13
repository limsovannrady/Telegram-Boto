from http.server import BaseHTTPRequestHandler
import json
import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_KEY = os.environ.get("SMSX_API_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5002402843"))

SMSX_BASE = "https://www.sms-x.org/stubs/handler_api.php"
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


def smsx(params: dict):
    try:
        resp = requests.get(SMSX_BASE, params={"api_key": API_KEY, **params}, timeout=10)
        return resp.text.strip()
    except Exception as e:
        return f"ERROR:{e}"


def get_balance():
    text = smsx({"action": "getBalance"})
    if text.startswith("ACCESS_BALANCE:"):
        return text.split(":")[1]
    return None


def handle_command(message):
    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id", 0)
    raw = message.get("text", "").strip()
    parts = raw.split()
    cmd = parts[0].lower().split("@")[0] if parts else ""

    if user_id != ADMIN_ID:
        tg_send(chat_id, "⛔ Access denied.")
        return

    if cmd == "/start":
        balance = get_balance()
        msg = (
            f"👤 *SMS-X Bot*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 Balance: *${balance or 'N/A'}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 *របៀបប្រើ:*\n"
            f"1️⃣ ទិញ number នៅ sms-x.org\n"
            f"2️⃣ Copy Order ID\n"
            f"3️⃣ ផ្ញើ `/check ORDER_ID` មក bot\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"`/check ORDER_ID` — check SMS code\n"
            f"`/balance` — មើល balance"
        )
        tg_send(chat_id, msg)

    elif cmd in ("/balance", "/account"):
        balance = get_balance()
        tg_send(chat_id, f"💰 Balance: *${balance}*" if balance else "⚠️ Cannot fetch balance.")

    elif cmd == "/check":
        if len(parts) < 2:
            tg_send(chat_id, "❗ Usage: `/check ORDER_ID`")
            return

        order_id = parts[1]
        result = smsx({"action": "getStatus", "id": order_id})

        if result.startswith("STATUS_OK:"):
            code = result.split(":", 1)[1]
            tg_send(chat_id, f"✅ *SMS Code:* `{code}`\n🆔 Order: `{order_id}`")
        elif result == "STATUS_WAIT_CODE":
            tg_send(chat_id, f"⏳ Still waiting for SMS on order `{order_id}`.\nTry again in a moment.")
        elif result == "NO_ACTIVATION":
            tg_send(chat_id, f"❌ Order `{order_id}` not found.")
        else:
            tg_send(chat_id, f"📋 Status: `{result}`")

    else:
        tg_send(chat_id, "❓ Unknown command. Use /start for help.")


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
