"""
処理概要:
    - Googleスプレッドシートの企業リストから検索プロンプトを生成し、OpenAI Chat Completions APIで検索結果テキストを取得します。
    - 対象列の「検索結果」を更新するだけの軽量ワークフローを1ファイルにまとめています。
使用方法:
    - `python search_single.py --config ../80_tools/config.json --web-search` などと実行してください。
    - `--query "キーワード"` を指定するとスプレッドシートを参照せず、OpenAIのWeb検索付き応答を1件取得します。
    - `--overwrite` で既存の検索結果セルを上書き、`--dry-run` で書き込みを抑止しログのみ確認できます。
    - OpenAI APIキーとGoogleサービスアカウントJSONを設定ファイル、または環境変数から指定してください。
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence
from urllib.parse import quote_plus

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import APIError, OpenAI

try:  # Optional dependency; fall back silently if unavailable.
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]


CURRENT_DIR = Path(__file__).resolve().parent

DEFAULT_MODEL = "GPT-5"
DEFAULT_MAX_TOKENS = 10000
DEFAULT_TEMPERATURE: Optional[float] = None
RESPONSES_MAX_TOKENS = 10000


# ------------------------------- Google Sheets ------------------------------


@dataclass
class GoogleSheetsClient:
    """Minimal wrapper for Google Sheets API service creation."""

    service_account_file: str
    scopes: Sequence[str] = (
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    )
    _service: Optional[object] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        credentials = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=list(self.scopes),
        )
        self._service = build("sheets", "v4", credentials=credentials)

    @property
    def service(self):  # pragma: no cover - simple accessor
        if self._service is None:
            raise RuntimeError("Google Sheets service is not initialized")
        return self._service

    def open_spreadsheet(self, spreadsheet_id: str) -> "SpreadsheetHandle":
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        return SpreadsheetHandle(client=self, spreadsheet_id=spreadsheet_id)


@dataclass
class SpreadsheetHandle:
    """Bind a client to a specific spreadsheet ID for value access."""

    client: GoogleSheetsClient
    spreadsheet_id: str

    def fetch_values(self, range_name: str) -> List[List[str]]:
        try:
            response = (
                self.client.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )
        except HttpError as err:  # pragma: no cover - network failures
            raise RuntimeError(f"Failed to fetch {range_name}: {err}") from err
        return response.get("values", [])

    def update_values(
        self,
        range_name: str,
        values: List[List[str]],
        value_input_option: str = "USER_ENTERED",
    ) -> int:
        body = {"values": values}
        try:
            response = (
                self.client.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )
        except HttpError as err:  # pragma: no cover - network failures
            raise RuntimeError(f"Failed to update {range_name}: {err}") from err
        return int(response.get("updatedCells", 0))


# -------------------------------- OpenAI client -----------------------------


def _collect_text(content) -> Iterable[str]:
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
    """Minimal client for OpenAI Chat Completions."""

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
        self._last_max_output_tokens = self.max_tokens

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
                except APIError as retry_err:  # pragma: no cover - upstream failure
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
                except APIError as retry_err:  # pragma: no cover - upstream failure
                    raise RuntimeError(f"OpenAI API error: {retry_err}") from retry_err
            raise RuntimeError(f"OpenAI API error: {err}") from err

    def _responses_truncation_message(self, response) -> str:
        limit = getattr(response, "max_output_tokens", None)
        if not isinstance(limit, int):
            if isinstance(response, dict):
                raw_limit = response.get("max_output_tokens")
                if isinstance(raw_limit, int):
                    limit = raw_limit
        if not isinstance(limit, int):
            limit = getattr(self, "_last_max_output_tokens", self.max_tokens)

        incomplete = getattr(response, "incomplete_details", None)
        if incomplete is None and isinstance(response, dict):
            incomplete = response.get("incomplete_details")
        reason = None
        if isinstance(incomplete, dict):
            reason = incomplete.get("reason") or incomplete.get("type")

        detail_text = f" (reason={reason})" if isinstance(reason, str) else ""

        return (
            "OpenAI web-search response hit max_output_tokens="
            f"{limit}{detail_text}; shorten or split the prompt to stay within {RESPONSES_MAX_TOKENS} tokens."
        )

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

    def search_and_generate(self, prompt: str) -> str:
        text, response = self.search_with_response(prompt)
        if text:
            if _contains_truncation(response):
                has_choices = hasattr(response, "choices") or (
                    isinstance(response, dict) and "choices" in response
                )
                if has_choices:
                    raise RuntimeError(
                        "OpenAI response was truncated (finish_reason=length); consider increasing max tokens or reducing prompt size."
                    )
                raise RuntimeError(self._responses_truncation_message(response))
            return text
        if _contains_truncation(response):
            raise RuntimeError(self._responses_truncation_message(response))
        raise RuntimeError("OpenAI API response did not contain any text output.")

    def search_with_response(self, prompt: str) -> tuple[str, object]:
        response = self._create_search_response(prompt)
        text = _extract_text_from_response(response)
        return text, response


def read_openai_key(explicit: Optional[str], env_var: str) -> Optional[str]:
    if explicit and explicit.strip():
        return explicit.strip()
    value = os.getenv(env_var, "").strip()
    return value or None


# ------------------------------ Prompt building -----------------------------


PLACEHOLDER_PREFIX = "{{"
PLACEHOLDER_SUFFIX = "}}"


@dataclass
class PromptBuilder:
    """Render prompts for company research."""

    search_template: str
    self_info: str

    def render_search_prompt(self, company: Mapping[str, str]) -> str:
        replacements = self._base_replacements(company)
        prompt = self._substitute(self.search_template, replacements)
        fallback = company.get("company_url") or company.get("company_name", "")
        return prompt.strip() or fallback

    def _substitute(self, template: str, replacements: Dict[str, str]) -> str:
        result = template
        for key, value in replacements.items():
            placeholder = f"{PLACEHOLDER_PREFIX}{key}{PLACEHOLDER_SUFFIX}"
            result = result.replace(placeholder, value)
        return result

    def _base_replacements(self, company: Mapping[str, str]) -> Dict[str, str]:
        return {
            "company_name": company.get("company_name", ""),
            "company_name_encoded": company.get("company_name_encoded", ""),
            "company_url": company.get("company_url", ""),
            "num_employees": company.get("num_employees", ""),
            "contact_form_url": company.get("contact_form_url", ""),
            "address": company.get("address", ""),
            "prefecture_id": company.get("prefecture_id", ""),
            "registered_company_name": company.get("registered_company_name", ""),
            "registered_company_name_encoded": company.get("registered_company_name_encoded", ""),
            "self_info": self.self_info,
        }


# --------------------------------- Config -----------------------------------


@dataclass
class SearchConfig:
    spreadsheet_id: str
    service_account_file: str
    search_prompt_range: str
    business_info_range: str
    output_sheet_name: str
    output_start_row: int
    openai_model: str
    openai_max_tokens: int
    openai_api_key: Optional[str]
    openai_api_key_env: str
    request_interval: float

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SearchConfig":
        ranges = data.get("ranges", {})  # type: ignore[arg-type]
        output = data.get("output", {})  # type: ignore[arg-type]
        openai_cfg = data.get("openai", {})  # type: ignore[arg-type]
        return cls(
            spreadsheet_id=str(data["spreadsheet_id"]),
            service_account_file=str(data["service_account_file"]),
            search_prompt_range=str(ranges["search_prompt_template"]),
            business_info_range=str(ranges["business_info"]),
            output_sheet_name=str(output.get("sheet_name", "結果")),
            output_start_row=int(output.get("start_row", 2)),
            openai_model=str(openai_cfg.get("model", DEFAULT_MODEL)),
            openai_max_tokens=int(openai_cfg.get("max_tokens", DEFAULT_MAX_TOKENS)),
            openai_api_key=str(openai_cfg.get("api_key", "")) or None,
            openai_api_key_env=str(openai_cfg.get("api_key_env", "OPENAI_API_KEY")),
            request_interval=float(
                data.get(
                    "request_interval",
                    openai_cfg.get("request_interval", 0),
                )
            ),
        )


def load_config(path: Path) -> SearchConfig:
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    config = SearchConfig.from_dict(raw)

    service_account = Path(config.service_account_file)
    if service_account.is_absolute() and service_account.exists():
        config.service_account_file = str(service_account)
        return config

    candidates: List[Path] = []
    candidates.append(path.parent / service_account)
    repo_root = CURRENT_DIR.parent.parent
    candidates.append(repo_root / service_account)
    candidates.append(CURRENT_DIR / service_account)
    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if env_path:
        candidates.append(Path(env_path))

    for candidate in candidates:
        try:
            if candidate.exists():
                config.service_account_file = str(candidate.resolve())
                return config
        except OSError:
            continue

    tried = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Service account file not found. Tried: {tried}"
    )


def read_single_cell(sheet: SpreadsheetHandle, range_name: str) -> str:
    values = sheet.fetch_values(range_name)
    if not values or not values[0]:
        raise ValueError(f"Range {range_name} is empty; check spreadsheet setup")
    return values[0][0]


# ------------------------------ Row processing ------------------------------


@dataclass
class ColumnIndexes:
    name: int
    url: int
    search_result: int
    num_employees: Optional[int] = None
    contact_form_url: Optional[int] = None
    address: Optional[int] = None
    prefecture_id: Optional[int] = None
    registered_company_name: Optional[int] = None


def _collect_header_values(row: List[str]) -> List[str]:
    return [cell.strip() for cell in row]


def _build_column_indexes(header: List[str]) -> ColumnIndexes:
    normalized = _collect_header_values(header)
    positions: Dict[str, List[int]] = {}
    for idx, value in enumerate(normalized):
        if not value:
            continue
        positions.setdefault(value, []).append(idx)

    def pick(label: str, *, required: bool = False, prefer_before: Optional[int] = None, prefer_after: Optional[int] = None) -> Optional[int]:
        candidates = positions.get(label, [])
        if prefer_before is not None:
            filtered = [idx for idx in candidates if idx < prefer_before]
            if filtered:
                candidates = filtered
        if prefer_after is not None:
            filtered = [idx for idx in candidates if idx > prefer_after]
            if filtered:
                candidates = filtered
        if not candidates:
            if required:
                raise ValueError(f"列 '{label}' がヘッダーにありません。スプレッドシートを確認してください。")
            return None
        return candidates[0]

    url_idx = pick("URL", required=True)
    if url_idx is None:
        raise AssertionError("URL column lookup failed")

    name_idx = pick("NAME", required=True, prefer_before=url_idx)
    if name_idx is None:
        raise AssertionError("NAME column lookup failed")

    search_idx = pick("検索結果", required=True, prefer_after=url_idx)
    if search_idx is None:
        raise AssertionError("検索結果 column lookup failed")

    num_idx = pick("NUM_EMPLOYEES", prefer_before=url_idx)
    contact_idx = pick("CONTACT_FORM_URL", prefer_after=url_idx)
    address_idx = pick("ADDRESS", prefer_after=url_idx)
    prefecture_idx = pick("PREFECTURE_ID", prefer_after=url_idx)

    registered_idx = None
    for label in ("REGISTERED_COMPANY_NAME", "REGISTERED_NAME", "登記業名"):
        candidate = pick(label, prefer_before=url_idx)
        if candidate is not None:
            registered_idx = candidate
            break

    return ColumnIndexes(
        name=name_idx,
        url=url_idx,
        search_result=search_idx,
        num_employees=num_idx,
        contact_form_url=contact_idx,
        address=address_idx,
        prefecture_id=prefecture_idx,
        registered_company_name=registered_idx,
    )


def _safe_get(row: List[str], index: Optional[int]) -> str:
    if index is None:
        return ""
    if index < len(row):
        return row[index].strip()
    return ""


def _column_number_to_a1(index: int) -> str:
    index += 1
    letters: List[str] = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


@dataclass
class CompanyRecord:
    row_number: int
    name: str
    url: str
    search_result: str
    num_employees: str = ""
    contact_form_url: str = ""
    address: str = ""
    prefecture_id: str = ""
    registered_company_name: str = ""

    def prompt_context(self) -> Dict[str, str]:
        return {
            "company_name": self.name,
            "company_name_encoded": _url_encode(self.name),
            "company_url": self.url,
            "num_employees": self.num_employees,
            "contact_form_url": self.contact_form_url,
            "address": self.address,
            "prefecture_id": self.prefecture_id,
            "registered_company_name": self.registered_company_name,
            "registered_company_name_encoded": _url_encode(self.registered_company_name),
        }


def _url_encode(value: str) -> str:
    if not value:
        return ""
    return quote_plus(value)


def _build_company_records(rows: List[List[str]], columns: ColumnIndexes, start_row: int) -> List[CompanyRecord]:
    records: List[CompanyRecord] = []
    for offset, row in enumerate(rows):
        name = _safe_get(row, columns.name)
        url = _safe_get(row, columns.url)
        if not name and not url:
            continue
        records.append(
            CompanyRecord(
                row_number=start_row + offset,
                name=name,
                url=url,
                search_result=_safe_get(row, columns.search_result),
                num_employees=_safe_get(row, columns.num_employees),
                contact_form_url=_safe_get(row, columns.contact_form_url),
                address=_safe_get(row, columns.address),
                prefecture_id=_safe_get(row, columns.prefecture_id),
                registered_company_name=_safe_get(row, columns.registered_company_name),
            )
        )
    return records


# ------------------------------- Main process -------------------------------


def run_search_job(
    config: SearchConfig,
    *,
    limit: Optional[int],
    overwrite: bool,
    dry_run: bool,
    use_web_search: bool,
) -> None:
    sheet_client = GoogleSheetsClient(service_account_file=config.service_account_file)
    sheet = sheet_client.open_spreadsheet(config.spreadsheet_id)

    search_template = read_single_cell(sheet, config.search_prompt_range)
    self_info = read_single_cell(sheet, config.business_info_range)
    builder = PromptBuilder(search_template=search_template, self_info=self_info)

    header_range = f"{config.output_sheet_name}!A1:ZZ1"
    header_rows = sheet.fetch_values(header_range)
    if not header_rows:
        raise ValueError("ヘッダー行が取得できませんでした。スプレッドシートの設定を確認してください。")
    columns = _build_column_indexes(header_rows[0])

    data_range = f"{config.output_sheet_name}!A{config.output_start_row}:ZZ"
    data_rows = sheet.fetch_values(data_range)
    company_records = _build_company_records(data_rows, columns, config.output_start_row)

    if limit is not None:
        company_records = company_records[:limit]

    if not company_records:
        print("処理対象の企業行がありません。シートのデータを確認してください。")
        return

    openai_key = read_openai_key(config.openai_api_key, config.openai_api_key_env)
    if not openai_key:
        raise ValueError("OpenAI API key is not configured. Provide openai.api_key or set environment variable.")

    openai_client = OpenAIClient(
        api_key=openai_key,
        model=config.openai_model,
        max_tokens=config.openai_max_tokens,
    )

    processed = 0
    for record in company_records:
        if not overwrite and record.search_result:
            print(f"[skip] Row {record.row_number} already has search result for {record.name or record.url}")
            continue

        try:
            context = record.prompt_context()
            search_prompt = builder.render_search_prompt(context)
            print(
                f"[prompt][row {record.row_number}] from sheet '{config.output_sheet_name}':\n{search_prompt}\n"
            )
            response_text = (
                openai_client.search_and_generate(search_prompt)
                if use_web_search
                else openai_client.generate_text(search_prompt)
            )
        except Exception as err:  # noqa: BLE001 - bubble up for visibility
            identifier = record.name or record.url or f"row {record.row_number}"
            print(f"[error] {identifier}: {err}")
            continue

        search_col = _column_number_to_a1(columns.search_result)
        target_range = f"{config.output_sheet_name}!{search_col}{record.row_number}"

        if dry_run:
            print(f"[dry-run] Would update {target_range}")
        else:
            updated_cells = sheet.update_values(target_range, [[response_text]])
            print(f"[write] Updated {target_range} ({updated_cells} cells)")

        processed += 1
        if config.request_interval > 0:
            time.sleep(config.request_interval)

    print(f"Completed generating search results for {processed} rows.")


def run_query(config: SearchConfig, query: str) -> None:
    """Run a single OpenAI web-search query and print the result."""

    if not query.strip():
        raise ValueError("Query must be a non-empty string")

    openai_key = read_openai_key(config.openai_api_key, config.openai_api_key_env)
    if not openai_key:
        raise ValueError("OpenAI API key is not configured. Provide openai.api_key or set environment variable.")

    client = OpenAIClient(
        api_key=openai_key,
        model=config.openai_model,
        max_tokens=config.openai_max_tokens,
    )

    print(f"[query] Running web search for: {query}")
    search_with_response = getattr(client, "search_with_response", None)
    print(f"[debug] search_with_response attr: {search_with_response!r}, callable={callable(search_with_response)}")
    response_obj = None
    if callable(search_with_response):
        text, response_obj = search_with_response(query)
    else:  # backwards compatibility fallback
        text = client.search_and_generate(query)

    if response_obj is not None:
        debug_payload = _dump_response(response_obj)
        if debug_payload:
            print("[debug] Raw API response:")
            print(debug_payload)
        if _contains_truncation(response_obj):
            raise RuntimeError(client._responses_truncation_message(response_obj))
    else:
        print("[debug] Raw API response: search_with_response unavailable (fallback path used)")

    if not text.strip():
        raise RuntimeError("OpenAI API response did not contain any text output. See [debug] for full payload.")

    print("[result]\n" + text)


def _dump_response(response: object) -> str:
    """Return a printable representation of an OpenAI SDK response."""

    data = None
    for attr in ("model_dump", "dict", "to_dict"):
        if hasattr(response, attr):
            try:
                data = getattr(response, attr)()
            except Exception:  # pragma: no cover - best effort
                data = None
            if data is not None:
                break

    if data is None and isinstance(response, dict):
        data = response

    if data is None:
        return str(response)

    try:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    except TypeError:
        return str(data)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate search results using OpenAI for spreadsheet rows.")
    parser.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N companies")
    parser.add_argument("--overwrite", action="store_true", help="既存の検索結果があっても上書きします")
    parser.add_argument("--dry-run", action="store_true", help="シート更新を行わず処理内容だけ表示します")
    parser.add_argument("--web-search", action="store_true", help="OpenAIのWeb検索ツールを使用します")
    parser.add_argument("--query", type=str, help="指定したキーワードでWeb検索付き応答を取得します")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    env_path = CURRENT_DIR.parent / ".env"
    if load_dotenv is not None:
        load_dotenv(env_path)

    args = parse_args(argv)
    config = load_config(args.config)
    if args.query:
        if not args.web_search:
            print("[info] --query 指定時は自動的にWeb検索を有効にします。")
        run_query(config, args.query)
        return

    run_search_job(
        config,
        limit=args.limit,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        use_web_search=args.web_search,
    )


if __name__ == "__main__":
    main()
