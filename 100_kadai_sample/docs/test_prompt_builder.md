# test_prompt_builder.py テスト仕様

## PromptBuilderSearchPromptTests.test_injects_company_name_placeholder
- **入力**
  - `PromptBuilder` の検索テンプレート: `Find info about {{company_name}}`
  - 企業辞書: `company_name="Acme Holdings"`
- **期待値**
  - 生成された検索プロンプトに生の会社名が埋め込まれる。

## PromptBuilderSearchPromptTests.test_uses_encoded_name_when_requested
- **入力**
  - 検索テンプレート: `https://search.example?q={{company_name_encoded}}`
  - 企業辞書: `company_name_encoded="Acme+Holdings"`
- **期待値**
  - URLクエリにエンコード済み会社名が挿入される。

## PromptBuilderSearchPromptTests.test_fallbacks_to_url_when_template_blank
- **入力**
  - 空白のみの検索テンプレート。
  - 企業辞書: `company_url="https://acme.example"`
- **期待値**
  - テンプレートが空の場合は会社URLを返す。
