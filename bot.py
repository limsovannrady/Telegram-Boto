import os
import threading
import requests
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_KEY = os.environ.get("SMSX_API_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5002402843"))

SMSX_BASE = "https://www.sms-x.org/stubs/handler_api.php"

flask_app = Flask(__name__)

bot_app = None
main_loop = None


def get_account_info():
    try:
        resp = requests.get(SMSX_BASE, params={
            "api_key": API_KEY,
            "action": "getBalance"
        }, timeout=10)
        text = resp.text.strip()
        if text.startswith("ACCESS_BALANCE:"):
            balance = text.split(":")[1]
            return balance
        return None
    except Exception:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
    balance = get_account_info()
    domain = os.environ.get("REPLIT_DEV_DOMAIN", "your-repl.replit.dev")
    webhook_url = f"https://{domain}/sms"
    if balance is not None:
        msg = (
            f"👤 *Account Info*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔑 API Key: `{API_KEY}`\n"
            f"💰 Balance: *${balance}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📡 Webhook URL:\n`{webhook_url}`\n\n"
            f"Set this URL in sms-x.org settings."
        )
    else:
        msg = (
            f"👤 *Account Info*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔑 API Key: `{API_KEY}`\n"
            f"⚠️ Could not fetch balance.\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📡 Webhook URL:\n`{webhook_url}`\n\n"
            f"Set this URL in sms-x.org settings."
        )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
    balance = get_account_info()
    if balance is not None:
        await update.message.reply_text(f"💰 Balance: *${balance}*", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Cannot fetch balance. Check your API key.")


def send_to_admin(msg: str):
    global bot_app, main_loop
    if bot_app is None or main_loop is None:
        print("Bot not ready yet")
        return

    async def _send():
        await bot_app.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            parse_mode="Markdown"
        )

    future = asyncio.run_coroutine_threadsafe(_send(), main_loop)
    try:
        future.result(timeout=10)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")


@flask_app.route("/sms", methods=["GET", "POST"])
def sms_webhook():
    if request.method == "GET":
        data = request.args
    else:
        data = request.form if request.form else request.get_json(force=True, silent=True) or {}

    phone = data.get("phone", data.get("number", ""))
    code = data.get("code", data.get("sms", data.get("text", "")))
    service = data.get("service", "")
    order_id = data.get("id", data.get("order_id", ""))

    msg = "📩 *SMS Received*\n━━━━━━━━━━━━━━━━\n"
    if service:
        msg += f"🛍️ Service: *{service}*\n"
    if order_id:
        msg += f"🆔 Order ID: `{order_id}`\n"
    if phone:
        msg += f"📞 Phone: `{phone}`\n"
    if code:
        msg += f"🔐 Code/SMS: *{code}*\n"
    msg += "━━━━━━━━━━━━━━━━"

    if not code and not phone:
        msg += f"\n📦 Raw data: `{dict(data)}`"

    print(f"Received SMS webhook: {dict(data)}")
    send_to_admin(msg)

    return jsonify({"status": "ok"})


@flask_app.route("/health")
def health():
    return jsonify({"status": "running"})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


async def main():
    global bot_app, main_loop
    main_loop = asyncio.get_running_loop()

    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("balance", balance_cmd))
    bot_app.add_handler(CommandHandler("account", balance_cmd))

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
    print(f"Bot started. Admin ID: {ADMIN_ID}")
    print(f"Webhook: https://{domain}/sms")

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
