import os
import httpx
from cryptography.fernet import Fernet

def cipher():
    key = os.getenv("ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is missing")
    return Fernet(key.encode())

def encrypt(value: str) -> str:
    return cipher().encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return cipher().decrypt(value.encode()).decode()

def mask_key(last4: str) -> str:
    return "••••••••••••" + last4

async def validate_and_encrypt(provider: str, api_key: str):
    if provider != "openrouter":
        return {"ok": False, "error": "Unsupported provider"}

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"}
            )
        if r.status_code >= 400:
            return {"ok": False, "error": f"API rejected the key (HTTP {r.status_code}). Check the key and try again."}
        return {
            "ok": True,
            "encrypted": encrypt(api_key),
            "last4": api_key[-4:]
        }
    except Exception as e:
        return {"ok": False, "error": "Could not reach the provider. Try again."}
