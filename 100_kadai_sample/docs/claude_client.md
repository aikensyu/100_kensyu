# claude_client.py 関数仕様

## ClaudeClient.from_env
- **入力**
  - `env_var` (`str`, 任意): APIキーを読む環境変数名。既定値は `ANTHROPIC_API_KEY`。
  - `model` (`str`, 任意): 使用するClaudeモデル。既定値は `claude-opus-4-1-20250805`。
  - `max_tokens` (`int`, 任意): 応答で許可する最大トークン数。既定値は `1024`。
- **出力**
  - `ClaudeClient`: APIキーを読み込んだクライアントインスタンス。

## ClaudeClient.generate_text
- **入力**
  - `prompt` (`str`): Claudeに送るユーザープロンプト。
- **出力**
  - `str`: Claudeから返されたテキスト応答。テキストブロックが無い場合はレスポンス全体のJSON文字列。

## read_api_key
- **入力**
  - `env_var` (`str`, 任意): 読み取る環境変数名。既定値は`ANTHROPIC_API_KEY`。
- **出力**
  - `Optional[str]`: APIキー文字列。環境変数が未設定なら `None`。
