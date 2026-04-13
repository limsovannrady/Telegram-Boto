# Vercel Deployment Guide

## Project Structure

```
/
├── api/
│   ├── webhook.py    ← Telegram bot webhook (commands: /start, /balance)
│   └── sms.py        ← SMS-X webhook (receives SMS → forwards to Telegram)
├── bot.py            ← Local dev bot (polling mode)
├── vercel.json       ← Vercel config
└── requirements.txt  ← Python dependencies
```

## Step 1 — Deploy to Vercel

```bash
npm i -g vercel
vercel --prod
```

Or connect your GitHub repo at https://vercel.com/new

---

## Step 2 — Set Environment Variables in Vercel

Go to **Vercel Dashboard → Project → Settings → Environment Variables** and add:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `SMSX_API_KEY` | `3dd71200967c1afb2a82bf21ee9c138c` |
| `ADMIN_ID` | `5002402843` |

---

## Step 3 — Register Telegram Webhook

After deploy, open this URL in your browser (replace `<your-domain>`):

```
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<your-domain>/api/webhook
```

Example:
```
https://api.telegram.org/bot1234567890:ABC.../setWebhook?url=https://my-bot.vercel.app/api/webhook
```

You should see: `{"ok":true,"result":true}`

---

## Step 4 — Set SMS-X Webhook

Go to your **sms-x.org** account settings and set the webhook URL to:

```
https://<your-domain>/api/sms
```

---

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/webhook` | POST | Telegram bot updates |
| `/api/sms` | GET / POST | SMS-X webhook — receives SMS, forwards to admin |

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Show account name, balance, and webhook URL |
| `/balance` | Show current SMS-X balance |
| `/account` | Same as /balance |
