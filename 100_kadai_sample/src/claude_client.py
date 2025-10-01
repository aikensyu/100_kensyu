"""
処理概要:
    - Anthropic Claude APIへ単発のメッセージを送るための軽量クライアント。
    - プロンプトとモデル名、最大トークン数を指定してテキスト応答を取得します。
使用方法:
    - 環境変数 `ANTHROPIC_API_KEY` にAPIキーを設定するか、`ClaudeClient` にapi_keyを渡します。
    - `ClaudeClient.generate_text(prompt)` を呼び出してレスポンス文字列を受け取ります。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-4-1-20250805"
DEFAULT_MAX_TOKENS = 1024


def _build_request_payload(prompt: str, model: str, max_tokens: int) -> Dict[str, object]:
    """Construct payload dictionary for Claude API."""
    return {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }


def _render_content_text(content: List[Dict[str, object]]) -> str:
    """Join text blocks returned by Claude into a single string."""
    text_blocks: List[str] = []
    for block in content:
        if block.get("type") == "text":
            text_blocks.append(str(block.get("text", "")))
    return "".join(text_blocks)


@dataclass
class ClaudeClient:
    """Minimal client for Anthropic Claude text generation."""

    api_key: str
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    api_url: str = API_URL

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("Claude API key is required")

    @classmethod
    def from_env(
        cls,
        env_var: str = "ANTHROPIC_API_KEY",
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> "ClaudeClient":
        """Create a client using an API key from environment variables."""
        key = os.getenv(env_var, "").strip()
        if not key:
            raise ValueError(f"Environment variable {env_var} is empty")
        return cls(api_key=key, model=model, max_tokens=max_tokens)

    def generate_text(self, prompt: str) -> str:
        """Send prompt to Claude and return the combined text content."""
        if not prompt:
            raise ValueError("Prompt must be a non-empty string")

        payload = _build_request_payload(prompt=prompt, model=self.model, max_tokens=self.max_tokens)
        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.api_url,
            data=data,
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            raise RuntimeError(f"Claude API error: {err.code} {err.reason}") from err
        except urllib.error.URLError as err:
            raise RuntimeError(f"Network error contacting Claude API: {err.reason}") from err

        document = json.loads(raw)
        content_blocks = document.get("content", [])
        if not isinstance(content_blocks, list):
            raise RuntimeError("Unexpected Claude response format: missing content array")

        text = _render_content_text(content_blocks)
        if text:
            return text

        return json.dumps(document, ensure_ascii=False)


def read_api_key(env_var: str = "ANTHROPIC_API_KEY") -> Optional[str]:
    """Read the API key from the environment if present."""
    key = os.getenv(env_var, "").strip()
    return key or None
