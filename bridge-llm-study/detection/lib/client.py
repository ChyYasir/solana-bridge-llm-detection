import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL = "deepseek-ai/DeepSeek-V3.2"
TEMPERATURE = 0
MAX_RETRIES = 8

_client = OpenAI(
    api_key=os.environ["DEEPINFRA_API_KEY"],
    base_url="https://api.deepinfra.com/v1/openai",
)


def ask(system_prompt: str, user_prompt: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = _client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 2 ** attempt
            print(f"  (model busy, retrying in {wait}s...)")
            time.sleep(wait)
