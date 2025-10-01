"""
処理概要:
    - サービスアカウント認証でGoogle Sheets APIへアクセスするユーティリティ。
    - スプレッドシートID単位のハンドルを作り、範囲の読み取りと書き込みを行います。
使用方法:
    - Google Cloudで発行したサービスアカウントJSONを用意し、`GoogleSheetsClient` にパスを渡します。
    - `client.open_spreadsheet(spreadsheet_id)` で `SpreadsheetHandle` を取得し、`fetch_values` や `update_values` を利用します。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DEFAULT_SCOPES: Sequence[str] = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
)


@dataclass
class GoogleSheetsClient:
    """Thin wrapper for Google Sheets API service creation."""

    service_account_file: str
    scopes: Sequence[str] = DEFAULT_SCOPES
    _service: Optional[object] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        credentials = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=list(self.scopes),
        )
        self._service = build("sheets", "v4", credentials=credentials)

    @property
    def service(self):  # pragma: no cover - accessor
        if self._service is None:
            raise RuntimeError("Google Sheets service is not initialized")
        return self._service

    def open_spreadsheet(self, spreadsheet_id: str) -> "SpreadsheetHandle":
        """Return a handle bound to the provided spreadsheet ID."""
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        return SpreadsheetHandle(client=self, spreadsheet_id=spreadsheet_id)


@dataclass
class SpreadsheetHandle:
    """Pair a Google Sheets client with a specific spreadsheet ID."""

    client: GoogleSheetsClient
    spreadsheet_id: str

    def fetch_values(self, range_name: str) -> List[List[str]]:
        """Return cell values from the given A1 range."""
        try:
            response = (
                self.client.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )
        except HttpError as err:
            raise RuntimeError(f"Failed to fetch {range_name}: {err}") from err
        return response.get("values", [])

    def update_values(
        self,
        range_name: str,
        values: List[List[str]],
        value_input_option: str = "USER_ENTERED",
    ) -> int:
        """Write values into the target range and return updated cell count."""
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
        except HttpError as err:
            raise RuntimeError(f"Failed to update {range_name}: {err}") from err
        return int(response.get("updatedCells", 0))

    def batch_update(self, requests: Iterable[dict]) -> None:
        """Send raw batchUpdate requests to the Sheets API."""
        body = {"requests": list(requests)}
        try:
            self.client.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body,
            ).execute()
        except HttpError as err:
            raise RuntimeError(f"Batch update failed: {err}") from err
