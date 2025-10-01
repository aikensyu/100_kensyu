# google_sheets_client.py 関数仕様

## GoogleSheetsClient.open_spreadsheet
- **入力**
  - `spreadsheet_id` (`str`): 対象スプレッドシートのID。
- **出力**
  - `SpreadsheetHandle`: 指定IDへ紐づいた操作ハンドル。

## SpreadsheetHandle.fetch_values
- **入力**
  - `range_name` (`str`): A1表記の範囲（例: `企業情報シート!A2:E100`）。
- **出力**
  - `List[List[str]]`: 指定範囲のセル値を行単位で並べた2次元リスト。未入力セルは空文字列。

## SpreadsheetHandle.update_values
- **入力**
  - `range_name` (`str`): A1表記の書き込み範囲。
  - `values` (`List[List[str]]`): 書き込むセル値。列数は範囲の列幅と合わせる。
  - `value_input_option` (`str`, 任意): 書き込みモード。既定は `USER_ENTERED`。
- **出力**
  - `int`: 更新されたセル数。

## SpreadsheetHandle.batch_update
- **入力**
  - `requests` (`Iterable[dict]`): Sheets APIのRawリクエスト辞書群。
- **出力**
  - `None`: 実行中にエラーが発生した場合は例外。
