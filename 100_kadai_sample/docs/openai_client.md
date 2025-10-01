# openai_client.py 関数仕様

## OpenAIClient.generate_text
- **入力**
  - `prompt` (`str`): OpenAIに送るユーザープロンプト。
- **出力**
  - `str`: Chat Completions APIが返した本文。`message.content` の `text` 部分を抽出し、`finish_reason` が `length` の場合は例外を送出します。温度パラメータが非対応のモデルでは自動的に既定温度（API側のデフォルト）で再試行します。

## OpenAIClient.search_and_generate
- **入力**
  - `prompt` (`str`): 検索ツールも有効にした状態で送信するプロンプト。
- **出力**
  - `str`: Web検索を利用した応答本文。`Responses` APIの `output_text` を含めてテキスト部分を抽出します。`max_output_tokens` は常に10000トークンに固定し、これを消費しても応答が完結しない場合はプロンプトの短縮／分割を促す例外を送出します。温度パラメータが非対応のモデルでは自動的に既定温度（API側のデフォルト）で再試行します。公式SDKのResponsesエンドポイント経由で `web_search` ツールを利用します。

## OpenAIClient.search_with_response
- **入力**
  - `prompt` (`str`): Web検索付きで送信するプロンプト。
- **出力**
  - `Tuple[str, object]`: 抽出済みテキストと Responses API が返した生オブジェクトのタプル。トークン上限（10000）に達した場合でもレスポンス本体を確認でき、例外メッセージで上限到達が明示されます。

## OpenAIClient.from_env
- **入力**
  - `env_var` (`str`, 任意): APIキーを読む環境変数名。既定値は `OPENAI_API_KEY`。
  - `model` (`str`, 任意): 使用するモデル名。既定値は `GPT-5`。
  - `max_tokens` (`int`, 任意): 応答で許可する最大トークン数。既定値は `10000`。
- **出力**
  - `OpenAIClient`: APIキーを読み込んだクライアントインスタンス。

## read_api_key
- **入力**
  - `env_var` (`str`, 任意): 読み取る環境変数名。既定値は `OPENAI_API_KEY`。
- **出力**
  - `Optional[str]`: APIキー文字列。環境変数が未設定なら `None`。
