"""
処理概要:
    - OpenAI Chat Completions / Responses API（公式Python SDK）を利用してテキストおよびWeb検索付きの応答を取得するクライアント。
    - 指定したプロンプトをユーザーメッセージとして送信し、モデルの応答からテキスト部分を抽出します。
使用方法:
    - 環境変数 `OPENAI_API_KEY` を設定するか、`OpenAIClient` に直接 `api_key` を渡してください。
    - `OpenAIClient.generate_text(prompt)` で通常の応答を取得します。
    - `OpenAIClient.search_and_generate(prompt)` でWeb検索ツールを有効化した応答を取得します。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from openai import APIError, OpenAI

DEFAULT_MODEL = "GPT-5"
DEFAULT_MAX_TOKENS = 10000
DEFAULT_TEMPERATURE: Optional[float] = None
RESPONSES_MAX_TOKENS = 10000


def _collect_text(content) -> Iterable[str]:
    """Yield textual fragments from Chat Completions content payloads."""
    if content is None:
        return
    if isinstance(content, str):
        stripped = content.strip()
        if stripped:
            yield stripped
        return
    if isinstance(content, list):
        for item in content:
            yield from _collect_text(item)
        return
    if isinstance(content, dict):
        c_type = content.get("type")
        if c_type in {"text", "output_text", "input_text"}:
            yield from _collect_text(content.get("text"))
            return
        if c_type == "tool_result":
            yield from _collect_text(content.get("content"))
            return
        for value in content.values():
            yield from _collect_text(value)
        return
    for attr in ("text", "content", "value"):
        if hasattr(content, attr):
            yield from _collect_text(getattr(content, attr))


def _extract_message_text(choice) -> str:
    """Return combined text for a single chat completion choice."""
    message = getattr(choice, "message", None)
    if message is None and isinstance(choice, dict):
        message = choice.get("message")
    if message is None:
        return ""

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    parts = list(_collect_text(content))
    if parts:
        return "\n".join(part for part in parts if part)

    refusal = getattr(message, "refusal", None)
    if not refusal and isinstance(message, dict):
        refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal.strip():
        return refusal.strip()

    return ""


def _extract_text_from_response(response) -> str:
    """Aggregate text from Chat Completions or Responses API payloads."""

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")
    if isinstance(output, list):
        texts: List[str] = []
        for item in output:
            texts.extend(_collect_text(item))
        if texts:
            return "\n".join(part for part in texts if part)

    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")
    if not isinstance(choices, list):
        return ""

    texts: List[str] = []
    for choice in choices:
        text = _extract_message_text(choice)
        if text:
            texts.append(text)
    return "\n".join(texts)


def _contains_truncation(response) -> bool:
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")
    if not isinstance(choices, list):
        status = getattr(response, "status", None)
        if status is None and isinstance(response, dict):
            status = response.get("status")
        if isinstance(status, str) and status.lower() == "incomplete":
            incomplete = getattr(response, "incomplete_details", None)
            if incomplete is None and isinstance(response, dict):
                incomplete = response.get("incomplete_details")
            if isinstance(incomplete, dict):
                reason = incomplete.get("reason") or incomplete.get("type")
                if isinstance(reason, str) and reason.lower() == "max_output_tokens":
                    return True
        return False
    for choice in choices:
        finish = getattr(choice, "finish_reason", None)
        if finish is None and isinstance(choice, dict):
            finish = choice.get("finish_reason")
        if isinstance(finish, str) and finish.lower() == "length":
            return True
    return False


def _is_temperature_unsupported(error: APIError) -> bool:
    """Return True if the error indicates temperature is not configurable."""

    param = getattr(error, "param", None)
    if isinstance(param, str) and param == "temperature":
        return True

    code = getattr(error, "code", None)
    if isinstance(code, str) and code == "unsupported_value":
        return True

    message = getattr(error, "message", None)
    if not isinstance(message, str):
        message = str(error)
    if not isinstance(message, str):
        return False
    lowered = message.lower()
    return "temperature" in lowered and "unsupported" in lowered


@dataclass
class OpenAIClient:
    """Minimal client for OpenAI chat completions."""

    api_key: str
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    _client: OpenAI = field(init=False, repr=False)
    _last_max_output_tokens: int = field(default=DEFAULT_MAX_TOKENS, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self._client = OpenAI(api_key=self.api_key)
        self._last_max_output_tokens = min(max(self.max_tokens, 1), RESPONSES_MAX_TOKENS)

    @classmethod
    def from_env(
        cls,
        env_var: str = "OPENAI_API_KEY",
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> "OpenAIClient":
        key = os.getenv(env_var, "").strip()
        if not key:
            raise ValueError(f"Environment variable {env_var} is empty")
        return cls(api_key=key, model=model, max_tokens=max_tokens)

    def _create_completion(self, prompt: str):
        if not prompt:
            raise ValueError("Prompt must be a non-empty string")

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "max_completion_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        try:
            return self._client.chat.completions.create(**kwargs)
        except APIError as err:
            if self.temperature is not None and _is_temperature_unsupported(err):
                fallback_kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
                try:
                    return self._client.chat.completions.create(**fallback_kwargs)
                except APIError as retry_err:
                    raise RuntimeError(f"OpenAI API error: {retry_err}") from retry_err
            raise RuntimeError(f"OpenAI API error: {err}") from err

    def _create_search_response(self, prompt: str):
        if not prompt:
            raise ValueError("Prompt must be a non-empty string")

        max_output_tokens = min(max(self.max_tokens, 1), RESPONSES_MAX_TOKENS)
        self._last_max_output_tokens = max_output_tokens

        kwargs = {
            "model": self.model,
            "input": prompt,
            "tools": [{"type": "web_search"}],
            "max_output_tokens": max_output_tokens,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        try:
            return self._client.responses.create(**kwargs)
        except APIError as err:
            if self.temperature is not None and _is_temperature_unsupported(err):
                fallback_kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
                try:
                    return self._client.responses.create(**fallback_kwargs)
                except APIError as retry_err:
                    raise RuntimeError(f"OpenAI API error: {retry_err}") from retry_err
            raise RuntimeError(f"OpenAI API error: {err}") from err

    def generate_text(self, prompt: str) -> str:
        response = self._create_completion(prompt)
        text = _extract_text_from_response(response)
        if text:
            if _contains_truncation(response):
                raise RuntimeError(
                    "OpenAI response was truncated (finish_reason=length); consider increasing max tokens or reducing prompt size."
                )
            return text
        raise RuntimeError("OpenAI API response did not contain any text output.")

    def search_with_response(self, prompt: str) -> tuple[str, object]:
        response = self._create_search_response(prompt)
        text = _extract_text_from_response(response)
        return text, response

    def search_and_generate(self, prompt: str) -> str:
        text, response = self.search_with_response(prompt)
        if text:
            if _contains_truncation(response):
                raise RuntimeError(self._responses_truncation_message(response))
            return text
        if _contains_truncation(response):
            raise RuntimeError(self._responses_truncation_message(response))
        raise RuntimeError("OpenAI API response did not contain any text output.")

    def _responses_truncation_message(self, response) -> str:
        limit = getattr(response, "max_output_tokens", None)
        if not isinstance(limit, int):
            if isinstance(response, dict):
                candidate = response.get("max_output_tokens")
                if isinstance(candidate, int):
                    limit = candidate
        if not isinstance(limit, int):
            limit = getattr(self, "_last_max_output_tokens", self.max_tokens)

        incomplete = getattr(response, "incomplete_details", None)
        if incomplete is None and isinstance(response, dict):
            incomplete = response.get("incomplete_details")
        detail = None
        if isinstance(incomplete, dict):
            detail = incomplete.get("reason") or incomplete.get("type")

        detail_text = f" (reason={detail})" if isinstance(detail, str) else ""
        return (
            "OpenAI web-search response hit max_output_tokens="
            f"{limit}{detail_text}; shorten or split the prompt to stay within {RESPONSES_MAX_TOKENS} tokens."
        )


def read_api_key(env_var: str = "OPENAI_API_KEY") -> Optional[str]:
    key = os.getenv(env_var, "").strip()
    return key or None
