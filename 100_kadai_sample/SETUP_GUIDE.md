# 🚀 プロジェクト起動準備ガイド

このガイドでは、プロジェクトを実行するために必要な準備を**ゼロから**順番に説明します。

---

## 📋 目次

1. [準備の全体像](#準備の全体像)
2. [必要なもの一覧](#必要なもの一覧)
3. [ステップ1: Python環境の確認](#ステップ1-python環境の確認)
4. [ステップ2: 外部ライブラリのインストール](#ステップ2-外部ライブラリのインストール)
5. [ステップ3: Google Cloud設定](#ステップ3-google-cloud設定)
6. [ステップ4: APIキーの取得](#ステップ4-apiキーの取得)
7. [ステップ5: 環境変数の設定](#ステップ5-環境変数の設定)
8. [ステップ6: 設定ファイルの編集](#ステップ6-設定ファイルの編集)
9. [ステップ7: Googleスプレッドシートの準備](#ステップ7-googleスプレッドシートの準備)
10. [ステップ8: 動作確認](#ステップ8-動作確認)
11. [トラブルシューティング](#トラブルシューティング)
12. [チェックリスト](#チェックリスト)

---

## 準備の全体像

```
┌─────────────────────────────────────────┐
│ ステップ1: Python環境確認               │
│ ✓ Python 3.8以上がインストール済みか   │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ2: ライブラリインストール       │
│ ✓ pip install -r requirements.txt      │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ3: Google Cloud設定             │
│ ✓ サービスアカウント作成                │
│ ✓ JSONキーダウンロード                  │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ4: APIキー取得                  │
│ ✓ OpenAI APIキー                        │
│ ✓ Anthropic APIキー                     │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ5: 環境変数設定                 │
│ ✓ .envファイル作成                      │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ6: 設定ファイル編集             │
│ ✓ config.jsonの設定                     │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ7: スプレッドシート準備         │
│ ✓ シート作成とヘッダー設定              │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│ ステップ8: 動作確認                     │
│ ✓ テスト実行                            │
└─────────────────────────────────────────┘
            ↓
        🎉 完了！
```

**所要時間**: 初回は約30分〜1時間

---

## 必要なもの一覧

### 💻 ソフトウェア

| 項目 | 必須/推奨 | 説明 |
|------|----------|------|
| Python 3.8以上 | **必須** | プログラムを実行するための言語 |
| pip | **必須** | Pythonライブラリ管理ツール（通常Pythonと一緒にインストールされる） |
| テキストエディタ | 推奨 | VS Code、Sublime Text、メモ帳など |
| ターミナル/コマンドプロンプト | **必須** | コマンドを実行するための画面 |

### 🔑 アカウント・認証情報

| 項目 | 必須/推奨 | 費用 | 説明 |
|------|----------|------|------|
| Googleアカウント | **必須** | 無料 | スプレッドシートとGoogle Cloud用 |
| Google Cloudプロジェクト | **必須** | 無料 | サービスアカウント作成用 |
| OpenAI APIキー | **必須** | 有料 | GPT-5を使用するため |
| Anthropic APIキー | **必須** | 有料 | Claude Opus 4.1を使用するため |

### 📁 ファイル

| 項目 | 場所 | 説明 |
|------|------|------|
| プロジェクトファイル | 既にダウンロード済み | このプロジェクトのすべてのコード |
| サービスアカウントJSON | Google Cloudからダウンロード | Google Sheets APIの認証に使用 |
| .envファイル | 自分で作成 | APIキーを保存 |
| config.json | 既に存在、編集が必要 | プロジェクトの設定 |

---

## ステップ1: Python環境の確認

### 1-1. Pythonのインストール確認

ターミナル（Macの場合）またはコマンドプロンプト（Windowsの場合）を開いて、以下を実行：

```bash
python --version
```

または

```bash
python3 --version
```

**期待される結果**:
```
Python 3.8.10
```
または
```
Python 3.10.5
```

**バージョンが3.8以上であればOK！** ✅

### 1-2. Pythonがない場合

#### Windows
1. [Python公式サイト](https://www.python.org/downloads/)からダウンロード
2. インストーラーを実行
3. **重要**: 「Add Python to PATH」にチェックを入れる
4. インストール完了後、コマンドプロンプトを再起動

#### Mac
```bash
# Homebrewを使う（推奨）
brew install python3

# または公式サイトからインストーラーをダウンロード
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### 1-3. pipの確認

```bash
pip --version
```

または

```bash
pip3 --version
```

**期待される結果**:
```
pip 23.0 from /usr/local/lib/python3.10/site-packages/pip (python 3.10)
```

---

## ステップ2: 外部ライブラリのインストール

### 2-1. プロジェクトディレクトリに移動

```bash
cd /Users/algo-q/Documents/GitHub/723_spreadsheet_autoform/05_sample
```

**確認方法**:
```bash
# 現在のディレクトリを表示
pwd

# ファイル一覧を表示
ls
# または（Windows）
dir
```

**期待される出力**:
```
80_tools/
docs/
secrets/
src/
PROJECT_WIKI.md
```

### 2-2. requirements.txtを確認

```bash
cat 80_tools/requirements.txt
```

**内容**:
```
google-api-python-client
google-auth
openai
```

### 2-3. ライブラリをインストール

```bash
pip install -r 80_tools/requirements.txt
```

または

```bash
pip3 install -r 80_tools/requirements.txt
```

**実行例**:
```
Collecting google-api-python-client
  Downloading google_api_python_client-2.95.0-py3-none-any.whl
Collecting google-auth
  Downloading google_auth-2.22.0-py2.py3-none-any.whl
Collecting openai
  Downloading openai-1.12.0-py3-none-any.whl
Installing collected packages: ...
Successfully installed google-api-python-client-2.95.0 google-auth-2.22.0 openai-1.12.0
```

### 2-4. 追加の推奨ライブラリ

```bash
# .envファイルを読み込むためのライブラリ（推奨）
pip install python-dotenv
```

### 2-5. インストール確認

```bash
pip list | grep google
pip list | grep openai
```

**期待される出力**:
```
google-api-python-client  2.95.0
google-auth              2.22.0
openai                   1.12.0
```

---

## ステップ3: Google Cloud設定

### 3-1. Google Cloudコンソールにアクセス

1. ブラウザで [Google Cloud Console](https://console.cloud.google.com/) を開く
2. Googleアカウントでログイン

### 3-2. 新しいプロジェクトを作成

1. 画面上部のプロジェクト選択メニューをクリック
2. 「新しいプロジェクト」をクリック
3. プロジェクト名を入力（例: `spreadsheet-autoform`）
4. 「作成」をクリック

### 3-3. Google Sheets APIを有効化

1. 左側のメニューから「APIとサービス」→「ライブラリ」を選択
2. 検索ボックスに「Google Sheets API」と入力
3. 「Google Sheets API」をクリック
4. 「有効にする」をクリック

### 3-4. サービスアカウントを作成

1. 左側のメニューから「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「サービスアカウント」をクリック
3. サービスアカウントの詳細を入力：
   - **名前**: `spreadsheet-bot`（任意）
   - **説明**: `Spreadsheet automation service account`（任意）
4. 「作成して続行」をクリック
5. ロールの選択：
   - 「編集者」を選択（または必要最小限の権限）
6. 「続行」→「完了」をクリック

### 3-5. サービスアカウントキー（JSON）をダウンロード

1. 作成したサービスアカウントをクリック
2. 「キー」タブをクリック
3. 「鍵を追加」→「新しい鍵を作成」をクリック
4. キーのタイプで「JSON」を選択
5. 「作成」をクリック
6. JSONファイルが自動的にダウンロードされます

**ダウンロードされるファイル名の例**:
```
spreadsheet-autoform-1234567890ab.json
```

### 3-6. JSONファイルを配置

1. ダウンロードしたJSONファイルを`secrets/`フォルダに移動
2. ファイル名を`service_account.json`に変更

```bash
# 例（Macの場合）
mv ~/Downloads/spreadsheet-autoform-*.json secrets/service_account.json

# 確認
ls secrets/
# 出力: service_account.json
```

### 3-7. サービスアカウントのメールアドレスを確認

JSONファイルを開いて、`client_email`の値をコピーしておく：

```bash
cat secrets/service_account.json | grep client_email
```

**出力例**:
```json
"client_email": "spreadsheet-bot@spreadsheet-autoform.iam.gserviceaccount.com",
```

このメールアドレスは後でスプレッドシートに共有するときに使います。

---

## ステップ4: APIキーの取得

### 4-1. OpenAI APIキーの取得

#### ステップA: OpenAIアカウント作成
1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. 「Sign up」をクリックしてアカウント作成
3. メールアドレスを確認

#### ステップB: APIキーを作成
1. ログイン後、右上のアイコンをクリック
2. 「View API keys」を選択
3. 「Create new secret key」をクリック
4. キー名を入力（例: `spreadsheet-autoform`）
5. 「Create secret key」をクリック
6. **重要**: 表示されたキーをコピー（一度しか表示されません）

**キーの形式**:
```
sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### ステップC: 使用料金の設定
1. 左側メニューから「Settings」→「Billing」を選択
2. クレジットカードを登録
3. 使用制限を設定（推奨: 月額$10〜$50）

**💰 料金目安**:
- GPT-5: 入力 $0.003/1Kトークン、出力 $0.015/1Kトークン
- Web検索付き: 追加料金が発生
- 企業1件あたり: 約$0.05〜$0.20（検索内容による）

### 4-2. Anthropic APIキーの取得

#### ステップA: Anthropicアカウント作成
1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. 「Sign up」をクリックしてアカウント作成
3. メールアドレスを確認

#### ステップB: APIキーを作成
1. ログイン後、「API Keys」セクションに移動
2. 「Create Key」をクリック
3. キー名を入力（例: `spreadsheet-autoform`）
4. 「Create Key」をクリック
5. **重要**: 表示されたキーをコピー（一度しか表示されません）

**キーの形式**:
```
sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### ステップC: クレジット購入
1. 左側メニューから「Billing」を選択
2. クレジットを購入（最低$5〜）

**💰 料金目安**:
- Claude Opus 4.1: 入力 $15/1Mトークン、出力 $75/1Mトークン
- 企業1件あたり: 約$0.05〜$0.15（営業文の長さによる）

---

## ステップ5: 環境変数の設定

### 5-1. .envファイルの作成

プロジェクトのルートディレクトリ（`05_sample`の親）または`src`の親ディレクトリに`.env`ファイルを作成します。

```bash
# プロジェクトルートに作成する場合
cd /Users/algo-q/Documents/GitHub/723_spreadsheet_autoform

# .envファイルを作成
touch .env
```

または

```bash
# 05_sampleに作成する場合
cd /Users/algo-q/Documents/GitHub/723_spreadsheet_autoform/05_sample

# .envファイルを作成
touch .env
```

### 5-2. .envファイルを編集

テキストエディタで`.env`ファイルを開き、以下を記入：

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic (Claude) API Key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**重要事項**:
- ✅ `=`の前後にスペースを入れない
- ✅ APIキーを`"`や`'`で囲まない
- ✅ 実際のAPIキーに置き換える
- ⚠️ このファイルを公開しない（GitHubなどにアップロードしない）

### 5-3. .gitignoreを確認

`.env`ファイルがGitで追跡されないように、`.gitignore`に追加：

```bash
# .gitignoreファイルを編集
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore
```

### 5-4. 環境変数の確認

```bash
# Macの場合
cat .env

# Windowsの場合
type .env
```

**期待される出力**:
```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## ステップ6: 設定ファイルの編集

### 6-1. config.jsonを開く

```bash
# 設定ファイルを確認
cat 80_tools/config.json
```

### 6-2. スプレッドシートIDを設定

スプレッドシートのURLから、IDを抽出します：

```
https://docs.google.com/spreadsheets/d/【ここがID】/edit
例: 1wmEom576X5Y8YBxwp6RFWhyPABFdZzYS6Qz_g1tBHzk
```

`config.json`の`spreadsheet_id`を更新：

```json
{
  "spreadsheet_id": "1wmEom576X5Y8YBxwp6RFWhyPABFdZzYS6Qz_g1tBHzk",
  ...
}
```

### 6-3. サービスアカウントファイルのパスを確認

```json
{
  ...
  "service_account_file": "../secrets/service_account.json",
  ...
}
```

**パスの説明**:
- `../secrets/service_account.json`: 相対パス（推奨）
- または絶対パス: `/Users/algo-q/Documents/GitHub/723_spreadsheet_autoform/05_sample/secrets/service_account.json`

### 6-4. その他の設定を確認

```json
{
  "spreadsheet_id": "あなたのスプレッドシートID",
  "service_account_file": "../secrets/service_account.json",
  "ranges": {
    "company_names": "'結果'!A2:A",
    "search_prompt_template": "'企業検索prompt'!A2",
    "message_prompt_template": "'フォーム文prompt'!A2",
    "business_info": "'自社情報'!A2"
  },
  "output": {
    "sheet_name": "結果",
    "start_row": 2
  },
  "openai": {
    "api_key_env": "OPENAI_API_KEY",
    "model": "gpt-5",
    "max_tokens": 5000
  },
  "anthropic": {
    "api_key_env": "ANTHROPIC_API_KEY",
    "model": "claude-opus-4-1-20250805",
    "max_tokens": 5000
  },
  "request_interval": 1.0
}
```

**設定のカスタマイズ**:

| 項目 | 説明 | 推奨値 |
|------|------|--------|
| `request_interval` | 各リクエスト間の待機時間（秒） | `1.0`〜`2.0` |
| `openai.max_tokens` | OpenAIの最大出力トークン | `5000`〜`10000` |
| `anthropic.max_tokens` | Claudeの最大出力トークン | `3000`〜`8000` |

---

## ステップ7: Googleスプレッドシートの準備

### 7-1. スプレッドシートを作成

1. [Google Sheets](https://sheets.google.com/)にアクセス
2. 「新しいスプレッドシートを作成」をクリック
3. スプレッドシート名を設定（例: `営業リスト自動化`）

### 7-2. 必要なシートを作成

以下の4つのシートを作成します：

#### シート1: 「結果」（メインデータ）

ヘッダー行（1行目）:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| NAME | URL | NUM_EMPLOYEES | 検索結果 | セールスレター | CONTACT_FORM_URL | ADDRESS |

**最小限の必須列**:
- `NAME` (A列): 企業名
- `URL` (B列): 企業のウェブサイトURL
- `検索結果` (D列): OpenAIが生成する企業情報
- `セールスレター` (E列): Claudeが生成する営業文

**オプションの列**:
- `NUM_EMPLOYEES`: 従業員数
- `CONTACT_FORM_URL`: お問い合わせフォームのURL
- `ADDRESS`: 住所
- `PREFECTURE_ID`: 都道府県ID
- `REGISTERED_COMPANY_NAME`: 登記社名

データ例（2行目以降）:

| A | B | C | D | E |
|---|---|---|---|---|
| 株式会社例 | https://example.co.jp | 100 | (空欄) | (空欄) |
| サンプル株式会社 | https://sample.jp | 50 | (空欄) | (空欄) |

#### シート2: 「企業検索prompt」

| A |
|---|
| プロンプトテンプレート（1行目は何でもOK） |
| {{company_name}}の最新情報を検索して、事業内容、主要製品、最近のニュースをまとめてください。 |

**A2セルに検索用のプロンプトテンプレートを記入**

プレースホルダー:
- `{{company_name}}`: 企業名
- `{{company_url}}`: 企業URL
- `{{num_employees}}`: 従業員数
- など

#### シート3: 「フォーム文prompt」

| A |
|---|
| プロンプトテンプレート（1行目は何でもOK） |
| 以下の企業情報と自社情報をもとに、丁寧な営業メールを作成してください。<br><br>【企業情報】<br>{{company_description}}<br><br>【自社情報】<br>{{self_info}}<br><br>企業の課題に寄り添った提案を含めてください。 |

**A2セルに営業文生成用のプロンプトテンプレートを記入**

追加のプレースホルダー:
- `{{company_description}}`: 検索結果（自動入力）
- `{{self_info}}`: 自社情報（次のシートから取得）

#### シート4: 「自社情報」

| A |
|---|
| 自社情報（1行目は何でもOK） |
| 当社は営業支援ツール「SalesPro」を提供している株式会社セールスです。中小企業向けに、営業活動の効率化と成約率向上をサポートしています。主な機能は、顧客管理、商談進捗管理、自動レポート生成です。 |

**A2セルに自社の紹介文を記入**

### 7-3. サービスアカウントに共有

1. スプレッドシート右上の「共有」をクリック
2. サービスアカウントのメールアドレスを入力
   - 例: `spreadsheet-bot@spreadsheet-autoform.iam.gserviceaccount.com`
3. 権限を「編集者」に設定
4. 「送信」をクリック

**⚠️ 重要**: この共有を忘れると、プログラムからスプレッドシートにアクセスできません！

### 7-4. スプレッドシートIDをコピー

URLからIDをコピー：
```
https://docs.google.com/spreadsheets/d/1wmEom576X5Y8YBxwp6RFWhyPABFdZzYS6Qz_g1tBHzk/edit
                                        ↑ ここがID ↑
```

このIDを`config.json`の`spreadsheet_id`に設定します（ステップ6で実施済み）。

---

## ステップ8: 動作確認

### 8-1. テスト実行（dry-run）

まずは、実際には書き込まない「dry-run」モードでテスト：

```bash
cd src
python fill_spreadsheet.py --config ../80_tools/config.json --limit 1 --dry-run
```

**期待される出力**:
```
[prompt][row 2] from sheet '結果':
株式会社例の最新情報を検索して...

[dry-run] Would update 結果!D2 and 結果!E2
Completed processing 0 companies.
```

**エラーがなければ成功！** ✅

### 8-2. 1件だけ実際に実行

```bash
python fill_spreadsheet.py --config ../80_tools/config.json --limit 1
```

**期待される出力**:
```
[prompt][row 2] from sheet '結果':
株式会社例の最新情報を検索して...

[write] Updated 結果!D2:E2 (2 cells)
Completed processing 1 companies.
```

### 8-3. スプレッドシートを確認

スプレッドシートの「結果」シートを開き、以下を確認：
- D2セル（検索結果）に企業情報が入力されている ✅
- E2セル（セールスレター）に営業文が入力されている ✅

### 8-4. Web検索付きで実行

```bash
python fill_spreadsheet.py --config ../80_tools/config.json --limit 1 --web-search
```

**Web検索機能を使うと**:
- より最新の情報を取得できる
- トークン消費が多くなる
- 実行時間が長くなる

### 8-5. 検索のみ実行（search_single.py）

営業文生成なしで、検索だけ実行：

```bash
python search_single.py --config ../80_tools/config.json --limit 1 --web-search
```

### 8-6. 単発クエリでテスト

スプレッドシートを使わず、1つのクエリをテスト：

```bash
python search_single.py --config ../80_tools/config.json --query "株式会社例について教えてください"
```

---

## トラブルシューティング

### エラー1: `ModuleNotFoundError: No module named 'XXX'`

**原因**: 必要なライブラリがインストールされていない

**解決方法**:
```bash
pip install -r 80_tools/requirements.txt
```

### エラー2: `Service account file not found`

**原因**: サービスアカウントJSONが見つからない

**解決方法**:
1. `secrets/service_account.json`が存在するか確認
   ```bash
   ls secrets/
   ```
2. パスが正しいか`config.json`を確認
3. ファイルが正しい場所にあるか確認

### エラー3: `API key is required` または `API key is empty`

**原因**: APIキーが設定されていない

**解決方法**:
1. `.env`ファイルが存在するか確認
   ```bash
   ls -la | grep .env
   ```
2. `.env`の内容を確認
   ```bash
   cat .env
   ```
3. APIキーが正しく設定されているか確認
4. 環境変数名が`config.json`と一致しているか確認

### エラー4: `Failed to fetch` または `Failed to update`

**原因**: Google Sheets APIの権限不足

**解決方法**:
1. スプレッドシートがサービスアカウントと共有されているか確認
2. サービスアカウントに「編集者」権限があるか確認
3. Google Sheets APIが有効化されているか確認

### エラー5: `列 'XXX' がヘッダーにありません`

**原因**: スプレッドシートのヘッダーに必要な列名がない

**解決方法**:
1. 「結果」シートの1行目に以下の列を追加：
   - `NAME`（必須）
   - `URL`（必須）
   - `検索結果`（必須）
   - `セールスレター`（必須）
2. 列名のスペルを確認（大文字・小文字も正確に）

### エラー6: `OpenAI API error: 401 Unauthorized`

**原因**: OpenAI APIキーが無効

**解決方法**:
1. APIキーが正しいか確認
2. OpenAIアカウントにログインして、APIキーを再生成
3. `.env`ファイルを更新

### エラー7: `Claude API error: 401`

**原因**: Anthropic APIキーが無効

**解決方法**:
1. APIキーが正しいか確認
2. Anthropicコンソールにログインして、APIキーを再生成
3. `.env`ファイルを更新

### エラー8: `OpenAI response was truncated`

**原因**: 出力トークン数が制限を超えた

**解決方法**:
1. `config.json`の`max_tokens`を増やす
   ```json
   "openai": {
     "max_tokens": 10000  // 5000から増やす
   }
   ```
2. プロンプトテンプレートを短くする

### エラー9: `insufficient_quota` または `rate_limit_exceeded`

**原因**: APIの使用制限または残高不足

**解決方法**:
1. **OpenAI**: Billingページでクレジット残高を確認、追加購入
2. **Anthropic**: Billingページでクレジット残高を確認、追加購入
3. `config.json`の`request_interval`を大きくする（例: `2.0`）

### エラー10: ファイルパスのエラー（Windows）

**原因**: Windowsのパス区切り文字が異なる

**解決方法**:
```json
// config.json で、バックスラッシュをスラッシュに変更
"service_account_file": "C:/Users/.../secrets/service_account.json"
// または
"service_account_file": "C:\\Users\\...\\secrets\\service_account.json"
```

---

## チェックリスト

すべて完了したか確認しましょう！

### ソフトウェア環境
- [ ] Python 3.8以上がインストールされている
- [ ] pipが使える
- [ ] 外部ライブラリがインストールされている
  - [ ] `google-api-python-client`
  - [ ] `google-auth`
  - [ ] `openai`
  - [ ] `python-dotenv`（推奨）

### Google Cloud
- [ ] Google Cloudプロジェクトを作成した
- [ ] Google Sheets APIを有効化した
- [ ] サービスアカウントを作成した
- [ ] サービスアカウントJSONをダウンロードした
- [ ] JSONファイルを`secrets/service_account.json`に配置した

### APIキー
- [ ] OpenAI APIキーを取得した
- [ ] Anthropic APIキーを取得した
- [ ] 両方のアカウントにクレジットがある

### 設定ファイル
- [ ] `.env`ファイルを作成した
- [ ] `.env`に両方のAPIキーを記入した
- [ ] `config.json`のスプレッドシートIDを更新した
- [ ] `config.json`のサービスアカウントファイルパスを確認した

### スプレッドシート
- [ ] Googleスプレッドシートを作成した
- [ ] 「結果」シートを作成し、ヘッダーを設定した
  - [ ] `NAME`列
  - [ ] `URL`列
  - [ ] `検索結果`列
  - [ ] `セールスレター`列
- [ ] 「企業検索prompt」シートを作成し、A2セルにテンプレートを記入した
- [ ] 「フォーム文prompt」シートを作成し、A2セルにテンプレートを記入した
- [ ] 「自社情報」シートを作成し、A2セルに自社情報を記入した
- [ ] サービスアカウントにスプレッドシートを共有した（編集者権限）
- [ ] テストデータを1〜2行入力した

### 動作確認
- [ ] `--dry-run`でエラーが出ない
- [ ] `--limit 1`で1件処理できた
- [ ] スプレッドシートに結果が書き込まれた

---

## 次のステップ

準備が完了したら、以下を試してみましょう：

### 1. 少量でテスト
```bash
# 最初の3件を処理
python src/fill_spreadsheet.py --config 80_tools/config.json --limit 3
```

### 2. Web検索機能を試す
```bash
# Web検索付きで実行
python src/fill_spreadsheet.py --config 80_tools/config.json --limit 3 --web-search
```

### 3. プロンプトを最適化
- スプレッドシートのプロンプトテンプレートを調整
- 単発クエリでテスト
  ```bash
  python src/search_single.py --config 80_tools/config.json --query "テストクエリ"
  ```

### 4. 本番実行
```bash
# 全件処理（--limitなし）
python src/fill_spreadsheet.py --config 80_tools/config.json --web-search
```

### 5. 既存結果を上書き
```bash
# 既に結果がある行も再処理
python src/fill_spreadsheet.py --config 80_tools/config.json --overwrite
```

---

## セキュリティのベストプラクティス

### 🔒 認証情報の管理

1. **絶対にGitHubにアップロードしないもの**:
   - `.env`ファイル
   - `secrets/service_account.json`
   - APIキー

2. **`.gitignore`に追加**:
   ```bash
   echo ".env" >> .gitignore
   echo "secrets/" >> .gitignore
   ```

3. **権限を制限**:
   ```bash
   # ファイルのアクセス権限を制限（Mac/Linux）
   chmod 600 .env
   chmod 600 secrets/service_account.json
   ```

4. **定期的にローテーション**:
   - APIキーを3〜6ヶ月ごとに再生成
   - 古いキーは削除

---

## コスト管理

### 💰 予算の設定

#### OpenAI
1. [OpenAI Platform](https://platform.openai.com/) にログイン
2. Settings → Billing → Usage limits
3. 月額上限を設定（例: $50）

#### Anthropic
1. [Anthropic Console](https://console.anthropic.com/) にログイン
2. Billing → Usage alerts
3. アラート設定（例: 残高が$10以下）

### 📊 使用量の確認

```bash
# 処理前に見積もり
# 企業100件、1件あたり$0.10として
# 100 × $0.10 = $10
```

### 💡 コスト削減のヒント

1. **`--dry-run`で事前確認**: 不要な実行を避ける
2. **`--limit`で段階的に**: 一度に全件処理しない
3. **`max_tokens`を最適化**: 必要以上に大きくしない
4. **Web検索を必要な時だけ**: トークン消費が多い
5. **`request_interval`を設定**: レート制限エラーを避ける

---

## サポートとリソース

### 📚 ドキュメント
- [PROJECT_WIKI.md](PROJECT_WIKI.md) - プロジェクト全体の解説
- `docs/` フォルダ - 各モジュールの詳細

### 🔗 公式ドキュメント
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Python dotenv](https://pypi.org/project/python-dotenv/)

### 🐛 問題が解決しない場合
1. エラーメッセージを詳しく確認
2. チェックリストを再確認
3. 各APIの公式ドキュメントを参照
4. ログファイルを確認（実装されている場合）

---

## まとめ

準備完了までの流れ：

1. ✅ **Python環境**: Python 3.8以上をインストール
2. ✅ **ライブラリ**: `pip install -r requirements.txt`
3. ✅ **Google Cloud**: サービスアカウント作成、JSON配置
4. ✅ **APIキー**: OpenAIとAnthropicのキーを取得
5. ✅ **環境変数**: `.env`ファイルにAPIキーを記入
6. ✅ **設定ファイル**: `config.json`を編集
7. ✅ **スプレッドシート**: 4つのシートを作成、サービスアカウントに共有
8. ✅ **動作確認**: `--dry-run`と`--limit 1`でテスト

**所要時間**: 初回は30分〜1時間

準備が完了したら、少量のデータでテストを開始し、徐々に本番運用に移行しましょう！

**🎉 準備完了です！頑張ってください！**

