"""
処理概要:
    - 指定したGoogleスプレッドシートからヘッダー付きのテーブルを読み込み、企業ごとの情報（NAME/URL など）を抽出します。
    - OpenAI gpt-5でWeb検索を使って検索結果テキストを生成し、Claude Opus 4.1 (2025-08-05) で営業フォーム文を作成して、該当行の「検索結果」「セールスレター」列へ書き込みます。
使用方法:
    - `python3 fill_spreadsheet.py --config ../80_tools/config.json` などと実行します。
    - `--web-search` オプションを付けるとOpenAIのWeb検索機能を使用します。
    - 事前にサービスアカウントJSONとOpenAI / ClaudeのAPIキーを設定ファイルか環境変数で指定してください。
    - スプレッドシートのヘッダー行に `NAME`, `URL`, `検索結果`, `セールスレター` が含まれている必要があります。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from claude_client import ClaudeClient, read_api_key as read_claude_key
from google_sheets_client import GoogleSheetsClient
from openai_client import OpenAIClient, read_api_key as read_openai_key
from prompt_builder import PromptBuilder


@dataclass
class AppConfig:
    """Typed view over JSON config file."""

    spreadsheet_id: str
    service_account_file: str
    company_names_range: str
    search_prompt_range: str
    message_prompt_range: str
    business_info_range: str
    output_sheet_name: str
    output_start_row: int
    openai_model: str
    openai_max_tokens: int
    openai_api_key: Optional[str]
    openai_api_key_env: str
    anthropic_model: str
    anthropic_max_tokens: int
    anthropic_api_key: Optional[str]
    anthropic_api_key_env: str
    request_interval: float

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AppConfig":
        ranges = data.get("ranges", {})  # type: ignore[arg-type]
        output = data.get("output", {})  # type: ignore[arg-type]
        openai = data.get("openai", {})  # type: ignore[arg-type]
        anthropic = data.get("anthropic", {})  # type: ignore[arg-type]
        return cls(
            spreadsheet_id=str(data["spreadsheet_id"]),
            service_account_file=str(data["service_account_file"]),
            company_names_range=str(ranges["company_names"]),
            search_prompt_range=str(ranges["search_prompt_template"]),
            message_prompt_range=str(ranges["message_prompt_template"]),
            business_info_range=str(ranges["business_info"]),
            output_sheet_name=str(output.get("sheet_name", "結果")),
            output_start_row=int(output.get("start_row", 2)),
            openai_model=str(openai.get("model", "gpt-5")),
            openai_max_tokens=int(openai.get("max_tokens", 10024)),
            openai_api_key=str(openai.get("api_key", "")) or None,
            openai_api_key_env=str(openai.get("api_key_env", "OPENAI_API_KEY")),
            anthropic_model=str(anthropic.get("model", "claude-opus-4-1-20250805")),
            anthropic_max_tokens=int(anthropic.get("max_tokens", 1024)),
            anthropic_api_key=str(anthropic.get("api_key", "")) or None,
            anthropic_api_key_env=str(anthropic.get("api_key_env", "ANTHROPIC_API_KEY")),
            request_interval=float(data.get("request_interval", anthropic.get("request_interval", openai.get("request_interval", 0)))),
        )


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    config = AppConfig.from_dict(data)

    # Resolve service account credential file to an absolute path for
    # robust execution regardless of current working directory.
    service_account = config.service_account_file
    resolved_path: Optional[Path] = None

    def _candidate_paths() -> List[Path]:
        candidates: List[Path] = []
        given = Path(service_account)
        if given.is_absolute():
            candidates.append(given)
        else:
            # 1) Relative to config file location
            candidates.append((path.parent / given))
            # 2) Relative to repository root (two levels up from src)
            repo_root = CURRENT_DIR.parent.parent
            candidates.append((repo_root / given))
            # 3) Relative to this module directory (rare but harmless)
            candidates.append((CURRENT_DIR / given))
        # 4) Environment variable fallback
        env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if env:
            candidates.append(Path(env))
        return candidates

    for candidate in _candidate_paths():
        try:
            if candidate.exists():
                resolved_path = candidate.resolve()
                break
        except OSError:
            # Ignore permission or transient FS errors when checking candidates
            continue

    if resolved_path is None:
        tried = ", ".join(str(p) for p in _candidate_paths())
        raise FileNotFoundError(
            f"Service account file not found. Tried: {tried}"
        )

    config.service_account_file = str(resolved_path)
    return config


def read_single_cell(sheet: "SpreadsheetHandle", range_name: str) -> str:
    values = sheet.fetch_values(range_name)
    if not values or not values[0]:
        raise ValueError(f"Range {range_name} is empty; check spreadsheet setup")
    return values[0][0]


@dataclass
class ColumnIndexes:
    """Hold zero-based column indexes resolved from the header row."""

    name: int
    url: int
    search_result: int
    sales_letter: int
    num_employees: Optional[int] = None
    contact_form_url: Optional[int] = None
    address: Optional[int] = None
    prefecture_id: Optional[int] = None
    registered_company_name: Optional[int] = None


@dataclass
class CompanyRecord:
    """Represent a single spreadsheet row with the required context."""

    row_number: int
    name: str
    url: str
    search_result: str
    sales_letter: str
    num_employees: str = ""
    contact_form_url: str = ""
    address: str = ""
    prefecture_id: str = ""
    registered_company_name: str = ""

    def prompt_context(self) -> Dict[str, str]:
        """Return replacements for prompt templates."""
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


def _collect_header_values(row: List[str]) -> List[str]:
    return [cell.strip() for cell in row]


def _url_encode(value: str) -> str:
    if not value:
        return ""
    return quote_plus(value)


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
            before_candidates = [idx for idx in candidates if idx < prefer_before]
            if before_candidates:
                candidates = before_candidates
        if prefer_after is not None:
            after_candidates = [idx for idx in candidates if idx > prefer_after]
            if after_candidates:
                candidates = after_candidates
        if not candidates:
            if required:
                raise ValueError(f"列 '{label}' がヘッダーにありません。スプレッドシートを確認してください。")
            return None
        return candidates[0]

    url_idx = pick("URL", required=True)
    if url_idx is None:  # for type checker; runtime guarded above
        raise AssertionError("URL column lookup failed")

    name_idx = pick("NAME", required=True, prefer_before=url_idx)
    if name_idx is None:
        raise AssertionError("NAME column lookup failed")
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

    search_idx = pick("検索結果", required=True, prefer_after=url_idx)
    if search_idx is None:
        raise AssertionError("検索結果 column lookup failed")
    sales_idx = pick("セールスレター", required=True, prefer_after=search_idx)
    if sales_idx is None:
        raise AssertionError("セールスレター column lookup failed")

    return ColumnIndexes(
        name=name_idx,
        url=url_idx,
        search_result=search_idx,
        sales_letter=sales_idx,
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


def _build_company_records(rows: List[List[str]], columns: ColumnIndexes, start_row: int) -> List[CompanyRecord]:
    records: List[CompanyRecord] = []
    for offset, row in enumerate(rows):
        name = _safe_get(row, columns.name)
        url = _safe_get(row, columns.url)
        if not name and not url:
            continue
        record = CompanyRecord(
            row_number=start_row + offset,
            name=name,
            url=url,
            search_result=_safe_get(row, columns.search_result),
            sales_letter=_safe_get(row, columns.sales_letter),
            num_employees=_safe_get(row, columns.num_employees),
            contact_form_url=_safe_get(row, columns.contact_form_url),
            address=_safe_get(row, columns.address),
            prefecture_id=_safe_get(row, columns.prefecture_id),
            registered_company_name=_safe_get(row, columns.registered_company_name),
        )
        records.append(record)
    return records


def run_job(config: AppConfig, limit: Optional[int], overwrite: bool, dry_run: bool, use_web_search: bool = False) -> None:
    client = GoogleSheetsClient(service_account_file=config.service_account_file)
    sheet = client.open_spreadsheet(config.spreadsheet_id)

    search_template = read_single_cell(sheet, config.search_prompt_range)
    message_template = read_single_cell(sheet, config.message_prompt_range)
    self_info = read_single_cell(sheet, config.business_info_range)

    builder = PromptBuilder(
        search_template=search_template,
        message_template=message_template,
        self_info=self_info,
    )

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

    openai_key = config.openai_api_key or read_openai_key(config.openai_api_key_env)
    if not openai_key:
        raise ValueError("OpenAI API key is not configured. Provide openai.api_key or set environment variable.")

    claude_key = config.anthropic_api_key or read_claude_key(config.anthropic_api_key_env)
    if not claude_key:
        raise ValueError("Claude API key is not configured. Provide anthropic.api_key or set environment variable.")

    openai_client = OpenAIClient(
        api_key=openai_key,
        model=config.openai_model,
        max_tokens=config.openai_max_tokens,
    )
    claude_client = ClaudeClient(
        api_key=claude_key,
        model=config.anthropic_model,
        max_tokens=config.anthropic_max_tokens,
    )

    total_processed = 0
    for record in company_records:
        if record.sales_letter and not overwrite:
            print(f"[skip] Row {record.row_number} already filled for {record.name or record.url}")
            continue

        try:
            company_context = record.prompt_context()

            search_result = record.search_result
            if overwrite or not search_result:
                search_prompt = builder.render_search_prompt(company_context)
                print(
                    f"[prompt][row {record.row_number}] from sheet '{config.output_sheet_name}':\n{search_prompt}\n"
                )
                if use_web_search:
                    search_result = openai_client.search_and_generate(search_prompt)
                else:
                    search_result = openai_client.generate_text(search_prompt)

            sales_letter = record.sales_letter if not overwrite else ""
            if overwrite or not sales_letter:
                message_prompt = builder.render_message_prompt(company_context, search_result)
                sales_letter = claude_client.generate_text(message_prompt)
        except Exception as err:  # noqa: BLE001 - surface upstream errors
            identifier = record.name or record.url or f"row {record.row_number}"
            print(f"[error] {identifier}: {err}")
            continue

        row_number = record.row_number
        search_col = _column_number_to_a1(columns.search_result)
        sales_col = _column_number_to_a1(columns.sales_letter)

        if dry_run:
            print(
                f"[dry-run] Would update {config.output_sheet_name}!{search_col}{row_number} "
                f"and {config.output_sheet_name}!{sales_col}{row_number}"
            )
        else:
            if columns.sales_letter == columns.search_result + 1:
                update_range = (
                    f"{config.output_sheet_name}!{search_col}{row_number}:{sales_col}{row_number}"
                )
                updated = sheet.update_values(update_range, [[search_result, sales_letter]])
                print(f"[write] Updated {update_range} ({updated} cells)")
            else:
                first_range = f"{config.output_sheet_name}!{search_col}{row_number}"
                second_range = f"{config.output_sheet_name}!{sales_col}{row_number}"
                updated_first = sheet.update_values(first_range, [[search_result]])
                updated_second = sheet.update_values(second_range, [[sales_letter]])
                print(
                    f"[write] Updated {first_range} ({updated_first} cells) and {second_range} "
                    f"({updated_second} cells)"
                )

        total_processed += 1
        if config.request_interval > 0:
            time.sleep(config.request_interval)

    print(f"Completed processing {total_processed} companies.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill spreadsheet using Claude outputs.")
    parser.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N companies")
    parser.add_argument("--overwrite", action="store_true", help="既存のフォーム文章結果があっても上書きします")
    parser.add_argument("--dry-run", action="store_true", help="シート更新を行わず処理内容だけ表示します")
    parser.add_argument("--web-search", action="store_true", help="OpenAIのWeb検索機能を使用して企業情報を検索します")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    # Load .env file from parent directory (01_codex)
    env_path = CURRENT_DIR.parent / ".env"
    load_dotenv(env_path)

    args = parse_args(argv)
    config = load_config(args.config)
    run_job(config, limit=args.limit, overwrite=args.overwrite, dry_run=args.dry_run, use_web_search=args.web_search)


if __name__ == "__main__":
    main()
