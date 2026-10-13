import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Provider: "deepinfra" (open-weight models) or "gemini" (Google, OpenAI-compatible endpoint).
# deepinfra/DeepSeek-V3.2 is the working default: Gemini refuses or hard-blocks
# security-audit prompts (blockReason OTHER / "cannot fulfill this request"), and
# gpt-oss-120b throttles heavily on the large source prompts. DeepSeek answers reliably.
PROVIDER = os.environ.get("PROVIDER", "deepinfra")
PROVIDERS = {
    "deepinfra": {
        "base_url": "https://api.deepinfra.com/v1/openai",
        "key_env": "DEEPINFRA_API_KEY",
        "default_model": "deepseek-ai/DeepSeek-V3.2",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-3.8-flash",
    },
}
_cfg = PROVIDERS[PROVIDER]

MODEL = os.environ.get("MODEL", _cfg["default_model"])
MODEL_SLUG = MODEL.split("/")[-1].lower()
TEMPERATURE = 0
MAX_RETRIES = 40  # patient: outlast transient provider overload periods
RETRY_WAIT_CAP = 20
REQUEST_TIMEOUT = 120  # seconds; a hung request fails fast and is retried

_client = OpenAI(
    api_key=os.environ[_cfg["key_env"]],
    base_url=_cfg["base_url"],
    timeout=REQUEST_TIMEOUT,
    max_retries=0,  # we handle retries ourselves so each wait is visible
)


def ask(system_prompt: str, user_prompt: str, model: str = MODEL) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = _client.chat.completions.create(
                model=model,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = min(2 ** attempt, RETRY_WAIT_CAP)
            print(f"  ({type(e).__name__}, retrying in {wait}s...)", flush=True)
            time.sleep(wait)


def results_path(root: Path, attack: str, task: str) -> Path:
    path = root / "detection" / "results" / f"{attack}-{task}-{MODEL_SLUG}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
