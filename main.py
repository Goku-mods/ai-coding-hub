import os
import asyncio
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from database import init_db, save_key, get_key_info, delete_key
from security import validate_and_encrypt, mask_key
from orchestrator import build_project

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
ADMIN_ID = os.getenv("ADMIN_ID", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
if not WEBAPP_URL:
    raise RuntimeError("WEBAPP_URL is missing")

telegram_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("⚡ OPEN AI CODING HUB",
                                       web_app=WebAppInfo(url=WEBAPP_URL))]]
    await update.message.reply_text(
        "⚡ AI CODING HUB\n\n"
        "Multiple AI roles work together to build and review your code.\n\n"
        "Press the button below to open the coding workspace.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = get_key_info(update.effective_user.id)
    if info:
        await update.message.reply_text(
            f"🔐 Provider: {info['provider']}\n"
            f"Status: {'🟢 Connected' if info['active'] else '🔴 Disconnected'}\n"
            f"Key: {mask_key(info['last4'])}"
        )
    else:
        await update.message.reply_text("🔑 No AI API connected yet. Open the Coding Hub and add one.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("status", status))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await telegram_app.initialize()
    await telegram_app.start()
    # Polling is used so the project can run on simple hosts without webhook setup.
    await telegram_app.updater.start_polling(drop_pending_updates=True)
    yield
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(title="AI Coding Hub", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="webapp"), name="static")

@app.get("/")
async def home():
    return FileResponse("webapp/index.html")

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/api/connect")
async def connect(request: Request):
    data = await request.json()
    telegram_id = int(data.get("telegram_id", 0))
    provider = data.get("provider", "openrouter")
    api_key = data.get("api_key", "").strip()

    if not telegram_id or not api_key:
        raise HTTPException(400, "Telegram ID and API key are required")
    if provider != "openrouter":
        raise HTTPException(400, "This build currently enables OpenRouter. Other providers can be added in providers/.")

    result = await validate_and_encrypt(provider, api_key)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)

    save_key(telegram_id, provider, result["encrypted"], result["last4"])
    return {"ok": True, "provider": provider, "masked": mask_key(result["last4"])}

@app.get("/api/key-status/{telegram_id}")
async def key_status(telegram_id: int):
    info = get_key_info(telegram_id)
    if not info:
        return {"connected": False}
    return {
        "connected": bool(info["active"]),
        "provider": info["provider"],
        "masked": mask_key(info["last4"])
    }

@app.delete("/api/key/{telegram_id}")
async def remove_key(telegram_id: int):
    delete_key(telegram_id)
    return {"ok": True}

@app.post("/api/build")
async def build(request: Request):
    data = await request.json()
    telegram_id = int(data.get("telegram_id", 0))
    prompt = data.get("prompt", "").strip()
    if not telegram_id or not prompt:
        raise HTTPException(400, "telegram_id and prompt are required")

    result = await build_project(telegram_id, prompt)
    if not result["ok"]:
        return JSONResponse(result, status_code=400)
    return result
