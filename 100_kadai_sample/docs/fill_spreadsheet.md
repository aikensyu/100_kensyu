# fill_spreadsheet.py 関数仕様

## AppConfig.from_dict
- **入力**
  - `data` (`Dict[str, object]`): JSON設定ファイルを読み込んだ辞書。
- **出力**
  - `AppConfig`: 設定項目を型付きで保持するインスタンス。`openai` と `anthropic` セクションから各APIのモデル名・トークン上限・APIキー情報を読み取る（OpenAIの `max_tokens` 既定値は10000で、Responses APIの `max_output_tokens` にそのまま適用されます）。

## load_config
- **入力**
  - `path` (`Path`): JSON設定ファイルへのパス。
- **出力**
  - `AppConfig`: ファイル内容を読み込んだ設定。`service_account_file` は絶対パスに解決されます。

### 補足: 認証ファイルのパス解決ルール
- 設定ファイルの `service_account_file` が絶対パスならそのまま使用。
- 相対パスの場合は以下の順に探索して最初に存在するものを採用します。
  1. 設定ファイルの位置からの相対パス
  2. リポジトリルート（`01_codex/src` から2つ上）からの相対パス
  3. このモジュール（`fill_spreadsheet.py`）と同一ディレクトリからの相対パス
  4. 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` が設定されていればそのパス

見つからない場合は、試行した候補一覧を含む `FileNotFoundError` を送出します。

## read_single_cell
- **入力**
  - `sheet` (`SpreadsheetHandle`): GoogleSheetsClientで生成したハンドル。
  - `range_name` (`str`): A1表記の単一セル範囲。
- **出力**
  - `str`: セルの文字列値。未設定なら例外を送出。

## ColumnIndexes
- **入力**: なし（データクラス）。
- **出力**
  - ヘッダー行から解決した列インデックスを保持するコンテナ。`name`, `url`, `search_result`, `sales_letter` は必須列、`num_employees`, `contact_form_url`, `address`, `prefecture_id`, `registered_company_name` はオプション。

## CompanyRecord
- **入力**: なし（データクラス）。
- **出力**
  - 1行分のシート情報と対応する `row_number` を保持する。`prompt_context()` はテンプレート置換用の辞書 (`Dict[str, str]`) を返す（`company_name`, `company_name_encoded`, `registered_company_name`, `registered_company_name_encoded` など）。

## _build_column_indexes
- **入力**
  - `header` (`List[str]`): ヘッダー行。
- **出力**
  - `ColumnIndexes`: `NAME`/`URL`/`検索結果`/`セールスレター` をはじめとした列の位置。存在しない必須列があれば `ValueError`。

## _collect_header_values
- **入力**
  - `row` (`List[str]`): 取得したヘッダー行。
- **出力**
  - `List[str]`: セル値をトリムしたヘッダー文字列リスト。

## _build_company_records
- **入力**
  - `rows` (`List[List[str]]`): データ行。
  - `columns` (`ColumnIndexes`): 解析済みヘッダー。
  - `start_row` (`int`): シート上の開始行番号。
- **出力**
  - `List[CompanyRecord]`: `NAME` または `URL` が入力されている行のみ抽出したリスト。

## _column_number_to_a1
- **入力**
  - `index` (`int`): 0始まりの列番号。
- **出力**
  - `str`: Sheets APIで利用できるA1形式の列記法。

## _safe_get
- **入力**
  - `row` (`List[str]`): データ行。
  - `index` (`Optional[int]`): 取得したい列インデックス。
- **出力**
  - `str`: 指定位置のセル値。列が存在しない、または `None` の場合は空文字列。

## run_job
- **入力**
  - `config` (`AppConfig`): 実行設定。
  - `limit` (`Optional[int]`): 処理する企業数の最大値。
  - `overwrite` (`bool`): 既存行の上書き可否。
  - `dry_run` (`bool`): 書き込みを抑止して内容のみ表示するか。
- **出力**
  - `None`: ヘッダーから `NAME`/`URL`/`検索結果`/`セールスレター` 列を検出し、
    - `{{company_url}}` や `{{company_name}}`, `{{registered_company_name}}`, `{{registered_company_name_encoded}}` を使ってOpenAI APIへ送る検索プロンプトを構築し検索結果テキストを生成、
    - 生成した検索プロンプトを標準出力へ `[prompt][row X]` 形式で表示し、シートから取得した値を確認できるようにしつつ、
    - 生成結果を含むテンプレートでClaude APIに営業フォーム文を生成、
    - 対応する「検索結果」「セールスレター」列へ書き込みます。既にセールスレター列が埋まっている場合は `overwrite` 指定がない限りスキップします。
  - OpenAIのWeb検索で `max_output_tokens=10000` に達した場合は例外で通知し、プロンプトの短縮や分割を促します。

## parse_args
- **入力**
  - `argv` (`Optional[List[str]]`): 引数リスト。省略時は `sys.argv`。
- **出力**
  - `argparse.Namespace`: CLI引数。

## main
- **入力**
  - `argv` (`Optional[List[str]]`): 引数リスト。
- **出力**
  - `None`: CLIエントリーポイント。
