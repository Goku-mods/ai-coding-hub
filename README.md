# AI Coding Hub — Telegram + Multi-AI

This is a ready starter project:
- Telegram bot
- Telegram Mini App UI
- Per-user API key connection
- API validation
- Encrypted local key storage
- Multi-agent coding workflow
- Project/session memory
- OpenRouter first; easy to add other OpenAI-compatible providers

## Owner setup
1. Create a bot with @BotFather using /newbot.
2. Deploy this folder to a Python/Docker host.
3. Set BOT_TOKEN, WEBAPP_URL, ENCRYPTION_KEY and ADMIN_ID.
4. Open @BotFather -> your bot -> Bot Settings -> Main Mini App and set WEBAPP_URL.
5. Start the service.
6. Open the bot and press /start.

## Generate ENCRYPTION_KEY
Run:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

## User flow
User opens bot -> Open Coding Hub -> API -> Add OpenRouter API key -> Connect.
The server tests the key, encrypts it, and the UI only shows a masked key.
The original API message is never stored by the bot.

## Important
The user supplies their own AI API key. The owner supplies only the Telegram bot token and server settings.
