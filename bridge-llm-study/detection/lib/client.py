import os
import time
from pathlib import Path

import httpx
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
# Stream responses: some reasoning models (GLM, Kimi) hang the non-streaming endpoint on large
# prompts because the gateway buffers the whole generation, but stream token-by-token fine.
# Two guards are needed because DeepInfra sometimes stalls a stream mid-generation while still
# sending keepalive bytes (which reset the read timeout): a per-read timeout for a dead
# connection, and a hard wall-clock deadline for a stalled-but-alive one.
READ_TIMEOUT = 90       # seconds with no bytes at all -> fail fast and retry
HARD_DEADLINE = 420     # seconds total per call -> abort a stalled stream and retry
# Generous cap so a reasoning model can finish its reasoning AND still emit the final answer;
# non-reasoning models stop well before this.
MAX_TOKENS = 16000
# Gemma 4 only thinks when its chat template is asked to; DeepInfra leaves it off by default.
EXTRA_BODY = {"google/gemma-4-31B-it": {"chat_template_kwargs": {"enable_thinking": True}}}

_client = OpenAI(
    api_key=os.environ[_cfg["key_env"]],
    base_url=_cfg["base_url"],
    timeout=httpx.Timeout(HARD_DEADLINE, connect=15.0, read=READ_TIMEOUT, write=15.0, pool=15.0),
    max_retries=0,  # we handle retries ourselves so each wait is visible
)


def ask(system_prompt: str, user_prompt: str, model: str = MODEL) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            stream = _client.chat.completions.create(
                model=model,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=True,
                extra_body=EXTRA_BODY.get(model),
                messages=([{"role": "system", "content": system_prompt}] if system_prompt else [])
                + [{"role": "user", "content": user_prompt}],
            )
            content, reasoning = [], []
            start = time.time()
            for chunk in stream:
                # Abort a stream that keeps the connection alive (resetting the read timeout)
                # but has stopped producing real output.
                if time.time() - start > HARD_DEADLINE:
                    stream.close()
                    raise APITimeoutError(request=httpx.Request("POST", _cfg["base_url"]))
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if getattr(delta, "content", None):
                    content.append(delta.content)
                rc = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
                if rc:
                    reasoning.append(rc)
            # The graded answer is the model's final message; fall back to reasoning only if a
            # model emitted nothing in the content channel.
            return "".join(content) or "".join(reasoning)
        except (
            RateLimitError, APITimeoutError, APIConnectionError, InternalServerError,
            # Raw httpx transport errors can leak through while consuming a stream (they are
            # only wrapped into the OpenAI types at request time, not mid-iteration).
            httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError,
        ) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = min(2 ** attempt, RETRY_WAIT_CAP)
            print(f"  ({type(e).__name__}, retrying in {wait}s...)", flush=True)
            time.sleep(wait)


def results_path(root: Path, attack: str, task: str) -> Path:
    path = root / "detection" / "results" / f"{attack}-{task}-{MODEL_SLUG}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
