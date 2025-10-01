# prompt_builder.py 関数仕様

## PromptBuilder.render_search_prompt
- **入力**
  - `company` (`Mapping[str, str]`): `company_name`, `company_url`, `num_employees` などを含む企業情報辞書。
- **出力**
  - `str`: `search_template` に辞書の値を差し込んだ文字列。テンプレート結果が空の場合は `company_url`、なければ `company_name` を返す。`{{registered_company_name}}` や `{{registered_company_name_encoded}}`, `{{company_name_encoded}}` といった追加プレースホルダも利用可能。

## PromptBuilder.render_message_prompt
- **入力**
  - `company` (`Mapping[str, str]`): テンプレート置換に利用する企業情報辞書。
  - `company_description` (`str`): OpenAIが返した検索結果テキスト。
- **出力**
  - `str`: `message_template` に `{{company_name}}`, `{{company_url}}`, `{{num_employees}}`, `{{address}}`, `{{prefecture_id}}`, `{{contact_form_url}}`, `{{company_description}}`, `{{self_info}}` などを差し込んだ営業文生成用プロンプト。

## PromptBuilder._base_replacements
- **入力**
  - `company` (`Mapping[str, str]`): プレースホルダへ渡す企業情報。
- **出力**
  - `Dict[str, str]`: `company_*` キー（`company_name`, `company_name_encoded`, `registered_company_name`, `registered_company_name_encoded` など）と `self_info` をまとめた置換辞書。`render_search_prompt` と `render_message_prompt` で共通利用。
