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
    text = message.get("text", "").strip()
    parts = text.split()
    cmd = parts[0].lower() if parts else ""

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
            f"📌 *Commands:*\n"
            f"`/buy SERVICE` — ទិញ number\n"
            f"`/check ORDER_ID` — check SMS\n"
            f"`/cancel ORDER_ID` — លុប order\n"
            f"`/balance` — មើល balance\n\n"
            f"*Service examples:* tg, wa, fb, ig"
        )
        tg_send(chat_id, msg)

    elif cmd in ("/balance", "/account"):
        balance = get_balance()
        if balance:
            tg_send(chat_id, f"💰 Balance: *${balance}*")
        else:
            tg_send(chat_id, "⚠️ Cannot fetch balance.")

    elif cmd == "/buy":
        if len(parts) < 2:
            tg_send(chat_id, "❗ Usage: `/buy SERVICE`\nExample: `/buy tg`")
            return

        service = parts[1].lower()
        tg_send(chat_id, f"⏳ Getting number for *{service}*...")

        result = smsx({"action": "getNumber", "service": service})
        print(f"[BUY] {result}")

        if result.startswith("ACCESS_NUMBER:"):
            r_parts = result.split(":")
            order_id = r_parts[1]
            phone = r_parts[2]
            msg = (
                f"📲 *Number Ready!*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🛍 Service: *{service}*\n"
                f"📞 Phone: `{phone}`\n"
                f"🆔 Order ID: `{order_id}`\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"⏳ Use `/check {order_id}` to get SMS code."
            )
            tg_send(chat_id, msg)
        elif result == "NO_NUMBERS":
            tg_send(chat_id, f"❌ No numbers available for *{service}*.")
        elif result == "NO_BALANCE":
            tg_send(chat_id, "❌ Insufficient balance.")
        else:
            tg_send(chat_id, f"❌ Error: `{result}`")

    elif cmd == "/check":
        if len(parts) < 2:
            tg_send(chat_id, "❗ Usage: `/check ORDER_ID`")
            return

        order_id = parts[1]
        result = smsx({"action": "getStatus", "id": order_id})
        print(f"[CHECK] {order_id}: {result}")

        if result.startswith("STATUS_OK:"):
            code = result.split(":", 1)[1]
            tg_send(chat_id, f"✅ *SMS Code:* `{code}`\n🆔 Order: `{order_id}`")
        elif result == "STATUS_WAIT_CODE":
            tg_send(chat_id, f"⏳ Still waiting for SMS...\nTry `/check {order_id}` again in a moment.")
        elif result in ("STATUS_CANCEL", "STATUS_WAIT_RETRY"):
            tg_send(chat_id, f"❌ Order `{order_id}` was cancelled.")
        else:
            tg_send(chat_id, f"📋 Status: `{result}`")

    elif cmd == "/cancel":
        if len(parts) < 2:
            tg_send(chat_id, "❗ Usage: `/cancel ORDER_ID`")
            return

        order_id = parts[1]
        smsx({"action": "setStatus", "id": order_id, "status": 8})
        tg_send(chat_id, f"✅ Order `{order_id}` cancelled.")

    else:
        tg_send(chat_id, "❓ Unknown command. Type /start for help.")


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
