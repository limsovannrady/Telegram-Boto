import os
import threading
import asyncio
import requests
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

active_orders = {}


def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID


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


def send_to_admin(msg: str):
    global bot_app, main_loop
    if not bot_app or not main_loop:
        return

    async def _send():
        await bot_app.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")

    future = asyncio.run_coroutine_threadsafe(_send(), main_loop)
    try:
        future.result(timeout=10)
    except Exception as e:
        print(f"Telegram send error: {e}")


def poll_order(order_id: str, label: str):
    print(f"[POLL] Start polling order {order_id}")
    attempts = 0
    max_attempts = 120  # 10 minutes (5s x 120)

    while attempts < max_attempts:
        if order_id not in active_orders:
            print(f"[POLL] Order {order_id} stopped.")
            return

        result = smsx({"action": "getStatus", "id": order_id})
        print(f"[POLL] {order_id}: {result}")

        if result.startswith("STATUS_OK:"):
            code = result.split(":", 1)[1]
            msg = (
                f"✅ *SMS Received!*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📝 Order: `{order_id}`"
                + (f"\n🏷 Label: {label}" if label else "") +
                f"\n🔐 *Code: {code}*\n"
                f"━━━━━━━━━━━━━━━━"
            )
            send_to_admin(msg)
            active_orders.pop(order_id, None)
            return

        elif result in ("STATUS_CANCEL", "NO_ACTIVATION"):
            send_to_admin(f"❌ Order `{order_id}` — cancelled or not found.")
            active_orders.pop(order_id, None)
            return

        attempts += 1
        threading.Event().wait(5)

    send_to_admin(f"⏰ Order `{order_id}` — timeout, no SMS after 10 minutes.")
    active_orders.pop(order_id, None)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    balance = get_balance()
    msg = (
        f"👤 *SMS-X Bot*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: *${balance or 'N/A'}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📌 *របៀបប្រើ:*\n"
        f"1️⃣ ទិញ number នៅ sms-x.org\n"
        f"2️⃣ Copy Order ID\n"
        f"3️⃣ ផ្ញើ `/watch ORDER_ID` មក bot\n"
        f"4️⃣ Bot poll ស្វ័យប្រវត្តិ — SMS ចូល ផ្ញើ Telegram ភ្លាម!\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📋 *Commands:*\n"
        f"`/watch ORDER_ID` — start poll\n"
        f"`/check ORDER_ID` — check ម្ដងៗ\n"
        f"`/stop ORDER_ID` — stop poll\n"
        f"`/orders` — active orders\n"
        f"`/balance` — មើល balance"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    balance = get_balance()
    if balance:
        await update.message.reply_text(f"💰 Balance: *${balance}*", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Cannot fetch balance.")


async def cmd_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Access denied.")
        return

    if not context.args:
        await update.message.reply_text(
            "❗ Usage: `/watch ORDER_ID`\nExample: `/watch 123456789`",
            parse_mode="Markdown"
        )
        return

    order_id = context.args[0]
    label = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    if order_id in active_orders:
        await update.message.reply_text(f"⚠️ Order `{order_id}` is already being watched.", parse_mode="Markdown")
        return

    result = smsx({"action": "getStatus", "id": order_id})
    if result == "NO_ACTIVATION":
        await update.message.reply_text(f"❌ Order `{order_id}` not found on sms-x.org.", parse_mode="Markdown")
        return

    if result.startswith("STATUS_OK:"):
        code = result.split(":", 1)[1]
        await update.message.reply_text(
            f"✅ *SMS already received!*\n🔐 Code: *{code}*",
            parse_mode="Markdown"
        )
        return

    active_orders[order_id] = {"label": label}
    msg = (
        f"👁 *Watching Order* `{order_id}`\n"
        + (f"🏷 Label: {label}\n" if label else "") +
        f"⏳ Polling every 5s — max 10 minutes.\n"
        f"SMS ចូលដល់ ខ្ញុំផ្ញើភ្លាម!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

    poll_thread = threading.Thread(target=poll_order, args=(order_id, label), daemon=True)
    poll_thread.start()


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Access denied.")
        return

    if not context.args:
        await update.message.reply_text("❗ Usage: `/check ORDER_ID`", parse_mode="Markdown")
        return

    order_id = context.args[0]
    result = smsx({"action": "getStatus", "id": order_id})

    if result.startswith("STATUS_OK:"):
        code = result.split(":", 1)[1]
        await update.message.reply_text(
            f"✅ *SMS Code:* `{code}`\n🆔 Order: `{order_id}`",
            parse_mode="Markdown"
        )
    elif result == "STATUS_WAIT_CODE":
        await update.message.reply_text(f"⏳ Waiting for SMS... Order `{order_id}`", parse_mode="Markdown")
    elif result == "NO_ACTIVATION":
        await update.message.reply_text(f"❌ Order `{order_id}` not found.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"📋 Status: `{result}`", parse_mode="Markdown")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Access denied.")
        return

    if not context.args:
        await update.message.reply_text("❗ Usage: `/stop ORDER_ID`", parse_mode="Markdown")
        return

    order_id = context.args[0]
    if order_id in active_orders:
        active_orders.pop(order_id)
        await update.message.reply_text(f"🛑 Stopped watching `{order_id}`.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Order `{order_id}` not in watch list.", parse_mode="Markdown")


async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Access denied.")
        return

    if not active_orders:
        await update.message.reply_text("📭 No active orders being watched.")
        return

    lines = ["📋 *Watching:*\n━━━━━━━━━━━━━━━━"]
    for oid, info in active_orders.items():
        label = info.get("label", "")
        lines.append(f"🆔 `{oid}`" + (f" — {label}" if label else ""))
    lines.append("━━━━━━━━━━━━━━━━")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


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
    bot_app.add_handler(CommandHandler("start", cmd_start))
    bot_app.add_handler(CommandHandler("balance", cmd_balance))
    bot_app.add_handler(CommandHandler("watch", cmd_watch))
    bot_app.add_handler(CommandHandler("check", cmd_check))
    bot_app.add_handler(CommandHandler("stop", cmd_stop))
    bot_app.add_handler(CommandHandler("orders", cmd_orders))

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print(f"Bot started. Admin: {ADMIN_ID}")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
