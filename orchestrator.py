import json
import os
import httpx
from database import get_key, save_project
from security import decrypt

# Change these model IDs whenever you want. They are the team's roles.
MODELS = {
    "architect": "openai/gpt-5.1",
    "coder": "openai/gpt-5.1",
    "reviewer": "openai/gpt-5.1",
    "debugger": "openai/gpt-5.1",
    "finalizer": "openai/gpt-5.1",
}

SYSTEMS = {
    "architect": """You are the software architect. Analyze the user's coding request.
Return a concise implementation plan, file tree, interfaces, dependencies and acceptance criteria.
Do not write the full implementation yet.""",
    "coder": """You are the main coding agent. Implement the requested project based on the architecture.
Return complete code for every necessary file. Prefer production-quality Python/HTML/CSS/JS.
Never leave TODO placeholders for core functionality.""",
    "reviewer": """You are a strict senior code reviewer. Inspect the proposed implementation against the
user request and architecture. Find functional bugs, security problems, missing files, bad assumptions,
and runtime issues. Give concrete fixes.""",
    "debugger": """You are the debugging agent. Given the architecture, code and review, produce corrected
complete files. Preserve working parts and fix the review findings.""",
    "finalizer": """You are the release engineer. Produce the final coherent project from the supplied
artifacts. Return a clean file tree and the final contents of files that changed. Remove accidental secrets,
TODOs, duplicate logic and broken references."""
}

async def call_model(api_key, model, system, user):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(f"Model request failed: HTTP {r.status_code}: {detail}")
        data = r.json()
        return data["choices"][0]["message"]["content"]

async def build_project(telegram_id: int, prompt: str):
    record = get_key(telegram_id)
    if not record:
        return {"ok": False, "error": "No API connected. Open API Manager and connect your OpenRouter key first."}

    api_key = decrypt(record["encrypted_key"])
    try:
        architecture = await call_model(
            api_key, MODELS["architect"], SYSTEMS["architect"],
            prompt
        )
        code = await call_model(
            api_key, MODELS["coder"], SYSTEMS["coder"],
            f"USER REQUEST:\n{prompt}\n\nARCHITECTURE:\n{architecture}"
        )
        review = await call_model(
            api_key, MODELS["reviewer"], SYSTEMS["reviewer"],
            f"USER REQUEST:\n{prompt}\n\nARCHITECTURE:\n{architecture}\n\nCODE:\n{code}"
        )
        fixed = await call_model(
            api_key, MODELS["debugger"], SYSTEMS["debugger"],
            f"USER REQUEST:\n{prompt}\n\nARCHITECTURE:\n{architecture}\n\nCODE:\n{code}\n\nREVIEW:\n{review}"
        )
        final = await call_model(
            api_key, MODELS["finalizer"], SYSTEMS["finalizer"],
            f"USER REQUEST:\n{prompt}\n\nARCHITECTURE:\n{architecture}\n\nORIGINAL CODE:\n{code}\n\nREVIEW:\n{review}\n\nFIXED CODE:\n{fixed}"
        )
        save_project(telegram_id, prompt, final)
        return {
            "ok": True,
            "architecture": architecture,
            "review": review,
            "result": final
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
