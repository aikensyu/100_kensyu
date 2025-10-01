# プロジェクト全体解説Wiki

## 📚 目次
1. [プロジェクト概要](#プロジェクト概要)
2. [システム構成図](#システム構成図)
3. [依存関係](#依存関係)
4. [各モジュールの詳細説明](#各モジュールの詳細説明)
5. [設定ファイル](#設定ファイル)
6. [実行方法](#実行方法)
7. [データフロー](#データフロー)
8. [初心者向け用語解説](#初心者向け用語解説)

---

## プロジェクト概要

このプロジェクトは、**Googleスプレッドシートに記載された企業リスト**を読み取り、各企業の情報をWeb検索し、その情報をもとに自動的にセールスレター（営業文）を生成して、結果をスプレッドシートに書き戻すシステムです。

### 主な機能
- 📊 Googleスプレッドシートから企業情報を自動取得
- 🔍 OpenAI（GPT-5）を使った企業情報のWeb検索
- 📝 Claude Opus 4.1を使ったセールスレターの自動生成
- 💾 生成した結果をスプレッドシートに自動書き込み

### 使用するAI
- **OpenAI GPT-5**: 企業情報の検索と要約
- **Claude Opus 4.1**: セールスレター（営業文）の作成

---

## システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                  Google スプレッドシート                      │
│  ┌─────────┬─────┬──────────┬────────────────┐             │
│  │ NAME    │ URL │ 検索結果  │ セールスレター │             │
│  ├─────────┼─────┼──────────┼────────────────┤             │
│  │ 企業A    │ ... │          │                │             │
│  │ 企業B    │ ... │          │                │             │
│  └─────────┴─────┴──────────┴────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
        ┌───────────────────────────────────────┐
        │   google_sheets_client.py             │
        │   （スプレッドシート読み書き）         │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │   fill_spreadsheet.py                 │
        │   （メイン処理・全体統合）             │
        └───────────────────────────────────────┘
                    ↙               ↘
    ┌──────────────────┐      ┌──────────────────┐
    │ openai_client.py │      │ claude_client.py │
    │ (企業情報検索)    │      │ (営業文生成)      │
    └──────────────────┘      └──────────────────┘
           ↓                           ↓
    [OpenAI API]              [Anthropic API]
      GPT-5 Web検索            Claude Opus 4.1
```

---

## 依存関係

### 📦 外部ライブラリ

プロジェクトは以下のPythonライブラリに依存しています（`80_tools/requirements.txt`）：

```
google-api-python-client  # Google Sheets APIとの通信
google-auth              # Google認証
openai                   # OpenAI APIとの通信
```

### 🔗 モジュール間の依存関係

```
fill_spreadsheet.py (メインプログラム)
├── claude_client.py        (Claudeとの通信)
├── openai_client.py        (OpenAIとの通信)
├── google_sheets_client.py (スプレッドシート操作)
└── prompt_builder.py       (プロンプト生成)

search_single.py (独立した検索専用プログラム)
└── (依存なし: すべての機能を1ファイルに含む)

test_prompt_builder.py (テスト)
└── prompt_builder.py
```

### 依存関係の特徴

1. **`fill_spreadsheet.py`**: 他のすべてのモジュールを使用するメインプログラム
2. **`search_single.py`**: 完全に独立した検索専用プログラム（他のモジュールに依存しない）
3. **各クライアント**: 独立しており、互いに依存していない

---

## 各モジュールの詳細説明

### 1. `google_sheets_client.py` - Googleスプレッドシート操作

**役割**: Googleスプレッドシートとの読み書きを担当します。

#### 主要なクラス

##### `GoogleSheetsClient`
- **説明**: Google Sheets APIに接続するための基本クライアント
- **初期化に必要なもの**: サービスアカウントのJSONファイル
- **主なメソッド**:
  - `open_spreadsheet(spreadsheet_id)`: スプレッドシートを開く

##### `SpreadsheetHandle`
- **説明**: 特定のスプレッドシートに対する操作を提供
- **主なメソッド**:
  - `fetch_values(range_name)`: 指定範囲のデータを読み取る
    - 例: `"結果!A2:D10"` → A2からD10までのセルを取得
  - `update_values(range_name, values)`: 指定範囲にデータを書き込む
    - 例: セルに検索結果を書き込む
  - `batch_update(requests)`: 複数の更新を一括実行

#### 使用例

```python
# クライアントを作成
client = GoogleSheetsClient(service_account_file="secrets/service_account.json")

# スプレッドシートを開く
sheet = client.open_spreadsheet("スプレッドシートID")

# データを読み取る
values = sheet.fetch_values("結果!A2:B10")
# 結果: [["企業A", "https://..."], ["企業B", "https://..."]]

# データを書き込む
sheet.update_values("結果!C2", [["検索結果テキスト"]])
```

---

### 2. `openai_client.py` - OpenAI API通信

**役割**: OpenAI（GPT-5）を使って企業情報の検索と要約を行います。

#### 主要なクラス

##### `OpenAIClient`
- **説明**: OpenAI APIとの通信を管理
- **初期化パラメータ**:
  - `api_key`: OpenAIのAPIキー
  - `model`: 使用するモデル（デフォルト: `"GPT-5"`）
  - `max_tokens`: 最大出力トークン数（デフォルト: 10,000）
  - `temperature`: 出力のランダム性（オプション）

##### 主なメソッド

###### `generate_text(prompt)`
- **説明**: 通常のチャット補完（Web検索なし）
- **入力**: プロンプト文字列
- **出力**: AIの応答テキスト

###### `search_and_generate(prompt)`
- **説明**: Web検索ツールを有効化した応答
- **入力**: 検索クエリを含むプロンプト
- **出力**: Web検索結果を含むAIの応答
- **特徴**: OpenAIが自動的にWeb検索を実行し、最新情報を取得

#### 内部処理の流れ

1. プロンプトを受け取る
2. OpenAI APIにリクエストを送信
3. レスポンスからテキスト部分を抽出
4. トークン制限チェック（切り詰められていないか確認）
5. テキストを返す

#### 使用例

```python
# クライアントを作成
client = OpenAIClient(api_key="your-api-key", model="gpt-5")

# 通常の生成
response = client.generate_text("企業Aについて教えてください")

# Web検索付き生成
search_result = client.search_and_generate("企業Aの最新ニュースを検索してください")
```

#### エラーハンドリング
- **temperature非対応エラー**: 一部のモデルでtemperatureが使えない場合、自動的に除外して再試行
- **トークン切り詰めエラー**: 出力が長すぎる場合にエラーを発生

---

### 3. `claude_client.py` - Claude API通信

**役割**: Anthropic Claude（Opus 4.1）を使ってセールスレター（営業文）を生成します。

#### 主要なクラス

##### `ClaudeClient`
- **説明**: Claude APIとの通信を管理
- **初期化パラメータ**:
  - `api_key`: AnthropicのAPIキー
  - `model`: 使用するモデル（デフォルト: `"claude-opus-4-1-20250805"`）
  - `max_tokens`: 最大出力トークン数（デフォルト: 1,024）

##### 主なメソッド

###### `generate_text(prompt)`
- **説明**: プロンプトを送信してテキストを生成
- **入力**: プロンプト文字列（企業情報と営業文テンプレートを含む）
- **出力**: 生成されたセールスレター

###### `from_env(env_var, model, max_tokens)`
- **説明**: 環境変数からAPIキーを読み取ってクライアントを作成
- **入力**: 環境変数名（デフォルト: `"ANTHROPIC_API_KEY"`）
- **出力**: `ClaudeClient`インスタンス

#### 内部処理の流れ

1. プロンプトを受け取る
2. リクエストペイロードを構築（JSON形式）
3. HTTPリクエストを送信（`urllib`を使用）
4. レスポンスをパース
5. テキストブロックを結合して返す

#### 使用例

```python
# 環境変数からクライアントを作成
client = ClaudeClient.from_env()

# テキスト生成
prompt = """
企業情報: 企業A、従業員100名、IT業界
自社情報: 当社は営業支援ツールを提供しています

上記の情報をもとに、企業Aへの営業文を作成してください。
"""
sales_letter = client.generate_text(prompt)
```

---

### 4. `prompt_builder.py` - プロンプト生成

**役割**: スプレッドシートから取得したテンプレートと企業情報を組み合わせて、AIに送るプロンプトを生成します。

#### 主要なクラス

##### `PromptBuilder`
- **説明**: プロンプトテンプレートの処理と変数置換を行う
- **初期化パラメータ**:
  - `search_template`: 企業検索用のプロンプトテンプレート
  - `message_template`: セールスレター生成用のプロンプトテンプレート
  - `self_info`: 自社情報（営業文に含める）

#### プレースホルダー（変数）

テンプレート内で使用できる変数：

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{{company_name}}` | 企業名 | `"株式会社例"` |
| `{{company_name_encoded}}` | URLエンコードされた企業名 | `"%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE%E4%BE%8B"` |
| `{{company_url}}` | 企業URL | `"https://example.co.jp"` |
| `{{num_employees}}` | 従業員数 | `"100"` |
| `{{contact_form_url}}` | お問い合わせフォームURL | `"https://example.co.jp/contact"` |
| `{{address}}` | 住所 | `"東京都渋谷区..."` |
| `{{prefecture_id}}` | 都道府県ID | `"13"` |
| `{{registered_company_name}}` | 登記社名 | `"株式会社例（登記名）"` |
| `{{registered_company_name_encoded}}` | URLエンコードされた登記社名 | `"..."` |
| `{{self_info}}` | 自社情報 | `"当社は..."` |
| `{{company_description}}` | 企業説明（検索結果） | `"企業Aは..."` |

#### 主なメソッド

###### `render_search_prompt(company)`
- **説明**: 企業検索用のプロンプトを生成
- **入力**: 企業情報の辞書
- **出力**: プレースホルダーが置換されたプロンプト文字列
- **フォールバック**: テンプレートが空の場合、企業URLまたは企業名を返す

###### `render_message_prompt(company, company_description)`
- **説明**: セールスレター生成用のプロンプトを生成
- **入力**: 
  - `company`: 企業情報の辞書
  - `company_description`: 企業の説明（検索結果）
- **出力**: プレースホルダーが置換されたプロンプト文字列

#### 使用例

```python
# ビルダーを作成
builder = PromptBuilder(
    search_template="{{company_name}}の最新情報を検索してください",
    message_template="企業情報: {{company_description}}\n自社: {{self_info}}\n\n営業文を作成:",
    self_info="当社は営業支援ツールを提供しています"
)

# 企業情報
company = {
    "company_name": "株式会社例",
    "company_url": "https://example.co.jp",
    "num_employees": "100"
}

# 検索プロンプトを生成
search_prompt = builder.render_search_prompt(company)
# 結果: "株式会社例の最新情報を検索してください"

# 営業文プロンプトを生成
company_description = "IT企業、従業員100名"
message_prompt = builder.render_message_prompt(company, company_description)
# 結果: "企業情報: IT企業、従業員100名\n自社: 当社は...\n\n営業文を作成:"
```

---

### 5. `fill_spreadsheet.py` - メインプログラム

**役割**: すべてのモジュールを統合し、全体の処理フローを制御します。

#### 主要なクラス

##### `AppConfig`
- **説明**: 設定ファイル（JSON）の内容を保持
- **主な設定項目**:
  - スプレッドシートID
  - サービスアカウントファイルのパス
  - 各種セル範囲の指定
  - OpenAI/Claudeの設定（モデル、トークン数など）
  - APIキーまたは環境変数名
  - リクエスト間隔

##### `CompanyRecord`
- **説明**: 1つの企業の行データを表現
- **主な属性**:
  - `row_number`: 行番号
  - `name`: 企業名
  - `url`: 企業URL
  - `search_result`: 検索結果（既存値）
  - `sales_letter`: セールスレター（既存値）
  - その他の企業情報（従業員数、住所など）

##### `ColumnIndexes`
- **説明**: ヘッダー行から各列の位置を保持
- **目的**: 列の順序が変わっても柔軟に対応

#### 主な関数

##### `load_config(path)`
- **説明**: JSONファイルから設定を読み込み
- **特徴**: サービスアカウントファイルのパスを自動解決

##### `run_job(config, limit, overwrite, dry_run, use_web_search)`
- **説明**: メイン処理を実行
- **パラメータ**:
  - `config`: 設定
  - `limit`: 処理する企業数の上限（Noneで全件）
  - `overwrite`: 既存結果を上書きするか
  - `dry_run`: 実際には書き込まず、ログだけ出力
  - `use_web_search`: OpenAIのWeb検索機能を使うか

#### 処理フロー

```
1. 設定ファイルを読み込む
   ↓
2. Google Sheetsに接続
   ↓
3. プロンプトテンプレートと自社情報を取得
   ↓
4. ヘッダー行を読み取り、列の位置を特定
   ↓
5. データ行を読み取り、CompanyRecordに変換
   ↓
6. 各企業について以下を実行:
   a. 既存のセールスレターがあれば（かつoverwriteなし）スキップ
   b. 検索プロンプトを生成
   c. OpenAIで企業情報を検索
   d. 営業文プロンプトを生成
   e. Claudeでセールスレターを生成
   f. 結果をスプレッドシートに書き込み
   g. 指定された間隔（request_interval）待機
   ↓
7. 完了
```

#### コマンドライン引数

```bash
python fill_spreadsheet.py \
  --config ../80_tools/config.json \  # 設定ファイル（必須）
  --limit 5 \                         # 最初の5件のみ処理（オプション）
  --overwrite \                       # 既存結果を上書き（オプション）
  --dry-run \                         # 書き込まず確認のみ（オプション）
  --web-search                        # Web検索を有効化（オプション）
```

#### 使用例

```bash
# 基本的な実行（Web検索なし）
python src/fill_spreadsheet.py --config 80_tools/config.json

# Web検索を使って実行
python src/fill_spreadsheet.py --config 80_tools/config.json --web-search

# 最初の3件だけテスト実行（実際には書き込まない）
python src/fill_spreadsheet.py --config 80_tools/config.json --limit 3 --dry-run

# 既存結果を上書きして再実行
python src/fill_spreadsheet.py --config 80_tools/config.json --overwrite
```

---

### 6. `search_single.py` - 検索専用プログラム

**役割**: 企業情報の検索のみを実行するスタンドアロンプログラム。セールスレターは生成しません。

#### 特徴
- **独立性**: 他のモジュールに依存せず、すべての機能を1ファイルに含む
- **軽量**: Claudeクライアントを含まない
- **柔軟**: スプレッドシート処理と単発クエリの両方に対応

#### 主な関数

##### `run_search_job(config, limit, overwrite, dry_run, use_web_search)`
- **説明**: スプレッドシートから企業リストを読み取り、検索結果を書き込む
- **処理内容**: `fill_spreadsheet.py`と類似だが、検索のみ

##### `run_query(config, query)`
- **説明**: 単一のクエリでWeb検索を実行（スプレッドシート不要）
- **用途**: APIの動作確認や手動検索

#### コマンドライン引数

```bash
python search_single.py \
  --config ../80_tools/config.json \  # 設定ファイル（必須）
  --limit 5 \                         # 最初の5件のみ処理（オプション）
  --overwrite \                       # 既存結果を上書き（オプション）
  --dry-run \                         # 書き込まず確認のみ（オプション）
  --web-search \                      # Web検索を有効化（オプション）
  --query "検索キーワード"             # 単発クエリ実行（オプション）
```

#### 使用例

```bash
# スプレッドシートの企業リストを検索
python src/search_single.py --config 80_tools/config.json --web-search

# 単発クエリでテスト
python src/search_single.py --config 80_tools/config.json --query "株式会社例の最新情報"
```

---

### 7. `test_prompt_builder.py` - ユニットテスト

**役割**: `PromptBuilder`の動作を検証するテストコード。

#### テストケース

1. **`test_injects_company_name_placeholder`**
   - プレースホルダー `{{company_name}}` が正しく置換されるか検証

2. **`test_uses_encoded_name_when_requested`**
   - URLエンコードされた企業名 `{{company_name_encoded}}` が正しく置換されるか検証

3. **`test_fallbacks_to_url_when_template_blank`**
   - テンプレートが空の場合、企業URLにフォールバックするか検証

#### 実行方法

```bash
# リポジトリルートから実行
python -m unittest src.test_prompt_builder

# または
cd src
python test_prompt_builder.py
```

---

## 設定ファイル

### `80_tools/config.json`

プロジェクトの設定を定義するJSONファイルです。

#### 設定項目の説明

```json
{
  // スプレッドシートのID（URLから取得）
  "spreadsheet_id": "1wmEom576X5Y8YBxwp6RFWhyPABFdZzYS6Qz_g1tBHzk",
  
  // サービスアカウントのJSONファイルパス
  "service_account_file": "../secrets/service_account.json",
  
  // スプレッドシート内の各範囲
  "ranges": {
    // 企業名のリスト（使用していない可能性）
    "company_names": "'結果'!A2:A",
    
    // 企業検索用のプロンプトテンプレート（単一セル）
    "search_prompt_template": "'企業検索prompt'!A2",
    
    // セールスレター生成用のプロンプトテンプレート（単一セル）
    "message_prompt_template": "'フォーム文prompt'!A2",
    
    // 自社情報（単一セル）
    "business_info": "'自社情報'!A2"
  },
  
  // 出力先の設定
  "output": {
    // データが格納されているシート名
    "sheet_name": "結果",
    
    // データの開始行（ヘッダーの次の行）
    "start_row": 2
  },
  
  // OpenAI（GPT-5）の設定
  "openai": {
    // APIキーを取得する環境変数名
    "api_key_env": "OPENAI_API_KEY",
    
    // 使用するモデル
    "model": "gpt-5",
    
    // 最大トークン数（オプション、デフォルト: 10000）
    "max_tokens": 5000
  },
  
  // Anthropic（Claude）の設定
  "anthropic": {
    // APIキーを取得する環境変数名
    "api_key_env": "ANTHROPIC_API_KEY",
    
    // 使用するモデル
    "model": "claude-opus-4-1-20250805",
    
    // 最大トークン数（オプション、デフォルト: 1024）
    "max_tokens": 5000
  },
  
  // リクエスト間隔（秒）
  // API制限を避けるため、各企業の処理後に待機する時間
  "request_interval": 1.0
}
```

#### 設定のカスタマイズ

1. **スプレッドシートIDの変更**:
   - スプレッドシートのURLから抽出: `https://docs.google.com/spreadsheets/d/{ここがID}/edit`

2. **APIキーの設定方法**:
   - 環境変数を使う（推奨）: `.env`ファイルに記載
   - 設定ファイルに直接記載（非推奨）: `"api_key": "your-key-here"` を追加

3. **リクエスト間隔の調整**:
   - API制限がある場合は `request_interval` を大きくする（例: `2.0`）
   - 制限がない場合は `0` にして高速化

---

## 実行方法

### 事前準備

#### 1. 必要なライブラリのインストール

```bash
cd 80_tools
pip install -r requirements.txt
```

#### 2. 環境変数の設定

`.env`ファイルを作成（プロジェクトルートまたは`src/`の親ディレクトリ）:

```bash
# OpenAI APIキー
OPENAI_API_KEY=sk-...

# Anthropic APIキー
ANTHROPIC_API_KEY=sk-ant-...
```

#### 3. サービスアカウントの配置

Google CloudでサービスアカウントJSONをダウンロードし、`secrets/service_account.json`に配置します。

### 実行例

#### パターン1: 基本的な実行

```bash
cd src
python fill_spreadsheet.py --config ../80_tools/config.json
```

#### パターン2: Web検索を有効化

```bash
python fill_spreadsheet.py --config ../80_tools/config.json --web-search
```

#### パターン3: テスト実行（最初の3件、書き込みなし）

```bash
python fill_spreadsheet.py --config ../80_tools/config.json --limit 3 --dry-run
```

#### パターン4: 検索のみ実行

```bash
python search_single.py --config ../80_tools/config.json --web-search
```

#### パターン5: 単発クエリでテスト

```bash
python search_single.py --config ../80_tools/config.json --query "株式会社例について"
```

---

## データフロー

### 全体のデータフロー

```
1. スプレッドシートからデータ取得
   ┌─────────────────────────────────────┐
   │ 結果シート                           │
   │ ┌──────┬─────┬─────┬──────┐        │
   │ │ NAME │ URL │ 検索 │ 営業文│        │
   │ ├──────┼─────┼─────┼──────┤        │
   │ │ 企業A│ ... │ (空) │ (空)  │        │
   │ └──────┴─────┴─────┴──────┘        │
   │                                     │
   │ ┌────────────────────┐              │
   │ │企業検索promptシート │              │
   │ │ テンプレート文字列  │              │
   │ └────────────────────┘              │
   │                                     │
   │ ┌────────────────────┐              │
   │ │フォーム文promptシート│              │
   │ │ テンプレート文字列  │              │
   │ └────────────────────┘              │
   │                                     │
   │ ┌────────────────────┐              │
   │ │自社情報シート       │              │
   │ │ 自社の説明文        │              │
   │ └────────────────────┘              │
   └─────────────────────────────────────┘
            ↓
2. プロンプト生成
   PromptBuilder
   ├─ 検索プロンプト: "{{company_name}}の最新情報"
   └─ 営業文プロンプト: "企業: {{company_description}}..."
            ↓
3. OpenAI（GPT-5）でWeb検索
   Input:  "株式会社例の最新情報を検索"
   Output: "株式会社例は...（検索結果の要約）"
            ↓
4. Claude（Opus 4.1）でセールスレター生成
   Input:  "企業情報: 株式会社例は...\n自社: 当社は...\n\n営業文を作成"
   Output: "拝啓、株式会社例 ご担当者様...(営業文)"
            ↓
5. スプレッドシートに書き込み
   ┌─────────────────────────────────────┐
   │ 結果シート                           │
   │ ┌──────┬─────┬─────────┬──────────┐ │
   │ │ NAME │ URL │ 検索結果 │ 営業文    │ │
   │ ├──────┼─────┼─────────┼──────────┤ │
   │ │ 企業A│ ... │ (検索結果)│(営業文)  │ │
   │ └──────┴─────┴─────────┴──────────┘ │
   └─────────────────────────────────────┘
```

### 各処理のデータ変換

#### 1. スプレッドシート → CompanyRecord

```
スプレッドシートの行:
["企業A", "https://a.com", "", "", "100"]

↓ 変換

CompanyRecord:
{
  row_number: 2,
  name: "企業A",
  url: "https://a.com",
  search_result: "",
  sales_letter: "",
  num_employees: "100"
}
```

#### 2. CompanyRecord → 検索プロンプト

```
CompanyRecord + テンプレート:
"{{company_name}}の最新情報を検索してください"

↓ 変換

検索プロンプト:
"企業Aの最新情報を検索してください"
```

#### 3. 検索プロンプト → OpenAI → 検索結果

```
Input:  "企業Aの最新情報を検索してください"

↓ OpenAI (Web検索付き)

Output: "企業Aは東京都に本社を置くIT企業で、従業員100名、
         主要製品は○○で、最近△△を発表しました。"
```

#### 4. 検索結果 → 営業文プロンプト

```
CompanyRecord + 検索結果 + テンプレート:
"企業情報: {{company_description}}
自社情報: {{self_info}}

上記をもとに営業文を作成してください"

↓ 変換

営業文プロンプト:
"企業情報: 企業Aは東京都に本社を置くIT企業で...
自社情報: 当社は営業支援ツールを提供しています...

上記をもとに営業文を作成してください"
```

#### 5. 営業文プロンプト → Claude → セールスレター

```
Input: (上記の営業文プロンプト)

↓ Claude Opus 4.1

Output: "拝啓、企業A ご担当者様

突然のご連絡失礼いたします。
当社は営業支援ツールを提供している○○株式会社と申します。

貴社が最近発表されました△△について拝見し、
当社のソリューションがお役に立てるのではないかと考え、
ご連絡させていただきました。

..."
```

---

## 初心者向け用語解説

### プログラミング用語

#### API（Application Programming Interface）
- **説明**: プログラム同士が通信するためのインターフェース
- **例**: OpenAI APIを使うと、自分のプログラムからGPT-5を呼び出せる

#### APIキー
- **説明**: APIを使用するための認証情報（パスワードのようなもの）
- **重要**: 秘密にする必要がある（公開しない）

#### クライアント
- **説明**: サービスに接続して操作を行うプログラムの部分
- **例**: `OpenAIClient`はOpenAI APIに接続して操作を行う

#### プロンプト
- **説明**: AIに送る指示文や質問文
- **例**: "株式会社例について教えてください"

#### トークン
- **説明**: AIが処理するテキストの単位（おおよそ単語や文字の塊）
- **重要**: APIの使用量や制限はトークン数で決まる
- **目安**: 日本語では1トークン = 約1〜2文字

#### レスポンス
- **説明**: APIから返ってくる応答データ
- **例**: OpenAIからの検索結果テキスト

#### データクラス（dataclass）
- **説明**: データを保持するための特別なクラス（Pythonの機能）
- **利点**: 簡潔に書けて、自動的に初期化メソッドなどが生成される

---

### Google Sheets用語

#### スプレッドシートID
- **説明**: Googleスプレッドシートを一意に識別するID
- **場所**: URLの中に含まれている
- **例**: `https://docs.google.com/spreadsheets/d/【ここがID】/edit`

#### A1記法（Range）
- **説明**: スプレッドシートのセル範囲を指定する記法
- **例**:
  - `A2`: A列2行目の単一セル
  - `A2:D10`: A列2行目からD列10行目までの範囲
  - `'結果'!A2:B10`: 「結果」シートのA2からB10までの範囲

#### サービスアカウント
- **説明**: プログラムがGoogle APIを使うための特別なアカウント
- **認証**: JSONファイルで認証（人間のパスワードは不要）
- **権限**: スプレッドシートに対して、明示的に共有する必要がある

---

### AI/LLM用語

#### GPT-5
- **説明**: OpenAIが提供する大規模言語モデル（LLM）の最新版
- **特徴**: 自然言語理解、生成、Web検索機能

#### Claude Opus 4.1
- **説明**: Anthropicが提供する大規模言語モデル
- **特徴**: 長文生成、複雑な指示の理解に優れる

#### Web検索（Web Search）
- **説明**: AIが自動的にインターネットを検索して最新情報を取得する機能
- **利点**: AIの学習データにない最新情報を取得できる

#### トークン制限
- **説明**: 1回のリクエストで処理できるトークン数の上限
- **対策**: プロンプトを短くする、max_tokensを調整する

#### Temperature（温度）
- **説明**: AIの出力のランダム性を制御するパラメータ
- **範囲**: 0（決定的）〜 1（ランダム）
- **注意**: 一部のモデルでは設定できない

---

### プロジェクト固有の用語

#### 検索結果
- **説明**: OpenAIが企業情報を検索・要約した結果
- **保存場所**: スプレッドシートの「検索結果」列
- **用途**: セールスレター生成の材料

#### セールスレター（営業文）
- **説明**: Claudeが生成した営業用の文章
- **保存場所**: スプレッドシートの「セールスレター」列
- **特徴**: 企業情報と自社情報をもとにカスタマイズされている

#### プレースホルダー
- **説明**: テンプレート内の変数（`{{変数名}}`の形式）
- **動作**: 実際の値に置き換えられる
- **例**: `{{company_name}}` → `"株式会社例"`

#### オーバーライト（Overwrite）
- **説明**: 既存のデータを上書きすること
- **オプション**: `--overwrite`フラグで有効化
- **用途**: 再実行時に結果を更新する

#### ドライラン（Dry Run）
- **説明**: 実際には実行せず、動作を確認するモード
- **オプション**: `--dry-run`フラグで有効化
- **利点**: 安全にテストできる

---

## トラブルシューティング

### よくあるエラーと対処法

#### 1. `API key is required`
- **原因**: APIキーが設定されていない
- **対処法**: 
  - 環境変数を確認（`.env`ファイル）
  - 設定ファイルに`api_key`を追加

#### 2. `Service account file not found`
- **原因**: サービスアカウントJSONが見つからない
- **対処法**:
  - パスが正しいか確認
  - ファイルが存在するか確認
  - 設定ファイルの`service_account_file`を更新

#### 3. `列 'XXX' がヘッダーにありません`
- **原因**: スプレッドシートのヘッダー行に必要な列名がない
- **対処法**: ヘッダー行に以下の列を追加
  - 必須: `NAME`, `URL`, `検索結果`, `セールスレター`

#### 4. `Failed to fetch/update`
- **原因**: Google Sheets APIの権限不足
- **対処法**:
  - スプレッドシートをサービスアカウントのメールアドレスと共有
  - サービスアカウントに「編集者」権限を付与

#### 5. `OpenAI response was truncated`
- **原因**: 出力トークン数が制限を超えた
- **対処法**:
  - 設定ファイルの`max_tokens`を増やす
  - プロンプトを短くする

#### 6. `temperature unsupported`
- **原因**: モデルがtemperatureパラメータに対応していない
- **対処法**: 自動的にフォールバック処理されるため、通常は無視してOK

---

## ベストプラクティス

### 1. 段階的なテスト

```bash
# ステップ1: dry-runで動作確認
python fill_spreadsheet.py --config config.json --limit 1 --dry-run

# ステップ2: 1件だけ実行
python fill_spreadsheet.py --config config.json --limit 1

# ステップ3: 少数で実行
python fill_spreadsheet.py --config config.json --limit 5

# ステップ4: 全件実行
python fill_spreadsheet.py --config config.json
```

### 2. API制限への配慮

- `request_interval`を適切に設定（推奨: 1.0〜2.0秒）
- 大量処理の場合は`--limit`で分割実行

### 3. コスト管理

- `--dry-run`で事前確認
- `max_tokens`を必要最小限に設定
- 不要なときは`--web-search`を使わない（トークン消費が多い）

### 4. データバックアップ

- 実行前にスプレッドシートをコピー
- 重要なデータは別途バックアップ

### 5. プロンプトの最適化

- テンプレートを段階的に改善
- 単発クエリ（`search_single.py --query`）でテスト
- 必要な情報だけを含めて簡潔に

---

## まとめ

このプロジェクトは、以下の流れで動作します：

1. **スプレッドシートから企業リストを取得**
2. **OpenAI（GPT-5）で企業情報を検索・要約**
3. **Claude（Opus 4.1）でセールスレターを生成**
4. **結果をスプレッドシートに書き戻す**

各モジュールは独立しており、それぞれが明確な役割を持っています。設定ファイルで柔軟にカスタマイズでき、コマンドラインオプションで様々な実行モードを選択できます。

初めて使う場合は、`--dry-run`と`--limit`を使って少量のデータでテストすることをお勧めします。

---

## 追加リソース

### 公式ドキュメント
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)

### 個別モジュールのドキュメント
- `docs/claude_client.md`
- `docs/openai_client.md`
- `docs/google_sheets_client.md`
- `docs/prompt_builder.md`
- `docs/fill_spreadsheet.md`
- `docs/search_single.md`

