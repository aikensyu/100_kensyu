# search_single.py 関数仕様

## run_search_job
- **入力**
  - `config` (`SearchConfig`): スプレッドシートやOpenAI設定を保持する構造体。
  - `limit` (`Optional[int]`): 先頭から処理する行数の上限。`None` なら全行対象。
  - `overwrite` (`bool`): 既存の「検索結果」セルを上書きするかどうか。
  - `dry_run` (`bool`): シート更新を行わずログのみ出力するフラグ。
  - `use_web_search` (`bool`): OpenAIのWeb検索ツールを利用するかどうか。
- **出力**
  - `None`: 処理は副作用としてシート更新および標準出力へのログを行います。

## run_query
- **入力**
  - `config` (`SearchConfig`): OpenAI設定を含む構造体。サービスアカウント設定は利用しません。
  - `query` (`str`): Web検索付きで実行するキーワードまたはプロンプト。
- **出力**
  - `None`: OpenAIから取得した検索結果テキストを標準出力に表示します。`OpenAIClient.search_with_response` が利用可能なら Responses API のRAWレスポンス(JSON形式)も表示し、利用不可の場合はフォールバック経路が選ばれた旨を出力します。レスポンスが `max_output_tokens`（10000）で打ち切られた場合はRAWレスポンスをログした上で、プロンプトの短縮／分割を促す例外を送出します。

## parse_args
- **入力**
  - `argv` (`Optional[List[str]]`): コマンドライン引数のリスト。`None` の場合は `sys.argv[1:]` を使用。
- **出力**
  - `argparse.Namespace`: `--config`, `--limit`, `--overwrite`, `--dry-run`, `--web-search`, `--query` を含む解析済み引数。

## main
- **入力**
  - `argv` (`Optional[List[str]]`): コマンドライン引数。省略時は標準の引数を利用。
- **出力**
  - `None`: `.env` の読み込み、設定ファイルの読込、`run_search_job` の実行を行います。

## PromptBuilder.render_search_prompt
- **入力**
  - `company` (`Mapping[str, str]`): `company_name` や `company_url` などプレースホルダを含む辞書。
- **出力**
  - `str`: プレースホルダ置換後の検索プロンプト文字列。テンプレートが空の場合はURLまたは社名を返します。
