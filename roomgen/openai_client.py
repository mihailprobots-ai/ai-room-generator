from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from .schemas import room_schema


class OpenAIClientError(RuntimeError):
    pass


def api_key_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def build_payload(prompt: str, model: str | None = None) -> dict:
    return {
        "model": model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "input": [
            {
                "role": "system",
                "content": "Return only a compact game room JSON object matching the provided schema.",
            },
            {"role": "user", "content": prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "room_spec",
                "schema": room_schema(),
                "strict": True,
            }
        },
    }


def request_room_spec(prompt: str) -> dict:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise OpenAIClientError("OPENAI_API_KEY is not configured. Copy .env.example to .env or export it.")

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(build_payload(prompt)).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OpenAIClientError(exc.read().decode("utf-8", errors="replace")[:1000]) from exc

    text = data.get("output_text")
    if not text:
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text = content.get("text")
                    break
    if not text:
        raise OpenAIClientError("OpenAI response did not contain output_text")
    return json.loads(text)


def load_prompt_template() -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "room_generator.txt"
    return path.read_text(encoding="utf-8")

