# Telegram SMS Bot

## Overview

A Telegram bot that connects to **sms-x.org** API to:
- Display account balance and info via commands
- Receive SMS notifications via webhook and forward them to admin

## Stack

- **Language**: Python 3.11 / 3.12
- **Local dev**: python-telegram-bot (polling mode) + Flask
- **Production (Vercel)**: Serverless functions via `api/` directory
- **HTTP client**: requests

## Project Structure

```
/
├── api/
│   ├── webhook.py    ← Telegram webhook handler (Vercel serverless)
│   └── sms.py        ← SMS-X webhook handler (Vercel serverless)
├── bot.py            ← Local development bot (polling + Flask)
├── vercel.json       ← Vercel deployment config
├── requirements.txt  ← Python deps for Vercel
├── pyproject.toml    ← Python deps for local dev
└── DEPLOY.md         ← Full deployment guide
```

## Environment Variables

| Name | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (secret) |
| `SMSX_API_KEY` | sms-x.org API key |
| `ADMIN_ID` | Telegram user ID to receive SMS |

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Show account info, balance, webhook URL |
| `/balance` | Show current balance |
| `/account` | Same as /balance |

## Endpoints (Vercel)

| Path | Method | Purpose |
|---|---|---|
| `/api/webhook` | POST | Receive Telegram updates |
| `/api/sms` | GET/POST | Receive SMS from sms-x.org |

## Deploy to Vercel

See `DEPLOY.md` for full instructions.
