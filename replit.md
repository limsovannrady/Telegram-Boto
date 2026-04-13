# Telegram SMS Bot

## Overview

A simple Telegram bot that connects to **sms-x.org** API to:
- Display account balance/info via commands
- Receive SMS webhook notifications from sms-x.org and forward them to the admin

## Stack

- **Language**: Python 3.11
- **Bot library**: python-telegram-bot
- **Web server**: Flask (receives SMS webhooks)
- **HTTP client**: requests

## Configuration

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Secret — Telegram bot token |
| `SMSX_API_KEY` | sms-x.org API key |
| `ADMIN_ID` | Telegram user ID to receive SMS notifications |

## Commands

| Command | Description |
|---|---|
| `/start` | Show account info, balance, and webhook URL |
| `/account` | Show account balance |
| `/balance` | Show account balance |

## Webhook Setup

The bot runs a Flask HTTP server. The webhook URL is:
```
https://<REPLIT_DEV_DOMAIN>/sms
```

Set this URL in your sms-x.org account settings so incoming SMS messages are forwarded to your Telegram admin account.

## Files

- `bot.py` — Main bot + Flask webhook server
- `pyproject.toml` — Python dependencies
