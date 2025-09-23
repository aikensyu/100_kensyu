# Claude Code コマンドリファレンス

## 🚀 概要

Claude Codeは、Anthropicが開発したAIペアプログラミングツールです。ターミナル上で自然言語による指示でコーディングタスクを実行できます。


---

## ⚙️ 基本コマンド

### セッション管理

```bash
# 基本的な起動
claude                              # 対話セッションを開始

# アップデートとセッション管理
claude update                       # 最新版にアップデート


### セッション内コマンド

| コマンド | 説明 |
|----------|------|
| `/clear` | 会話履歴とコンテキストをリセット（高速） |
### 🎯 ショートカットキー

| キー | 機能 |
|------|------|
| **Esc × 2** | 過去のメッセージ一覧を表示・ジャンプ |
| **↑** | チャット履歴を遡る（前セッション含む） |
| **Esc** | Claudeの実行を停止 |
| **#** | CLAUDE.mdに指示を自動追加 |
| **Shift + ドラッグ** | ファイルを適切に参照 |
| **Ctrl + Shift** | 特殊機能（詳細は使用時に確認） |

> 💡 **Tips**: Ctrl+Cは完全終了、Command+VではなくControl+Vで画像貼り付け

---

## 🔧 CLIフラグオプション

### 基本設定

```bash
--add-dir <path>                    # 追加の作業ディレクトリを指定
--model <sonnet|opus>               # 使用するAIモデルを選択
--output-format json                # JSON形式での構造化応答
```

### 権限管理

```bash
--dangerously-skip-permissions      # 全権限プロンプトをスキップ
```



## 🧠 高度な機能

### Plan Mode（自走モード）

拡張思考機能で包括的な戦略を作成：

**適用場面:**
- ✅ 新機能の開始時
- ✅ 複雑な課題への取り組み
- ✅ コードのリファクタリング

**思考深度の制御:**

| 指示 | 分析レベル |
|------|------------|
| `"think"` | 基本的な分析 |
| `"think hard"` | 深い分析 |
| `"ultrathink"` | 最大深度の分析 |

### スラッシュコマンド

`.claude/commands`フォルダにMarkdownファイルでプロンプトテンプレートを保存：

- `/`入力でコマンドメニュー表示
- gitチェックインでチーム共有可能

### MCP（Model Context Protocol）

```bash
claude mcp                          # MCPサーバーの設定
```

**接続方法:**
1. プロジェクト設定内
2. チェックイン済み`.mcp.json`ファイル

---

## 📄 CLAUDE.md ファイルガイド

### 📍 概要

CLAUDE.mdは、プロジェクトの設定情報を記載する特別なファイルです。Claudeが会話開始時に自動読み込みし、コンテキストとして活用します。

### 📂 配置場所（優先順位順）

| 順位 | 場所 | ファイル名 | 用途 |
|------|------|------------|------|
| 1 | リポジトリルート | `CLAUDE.md` | チーム共有（推奨） |
| 2 | リポジトリルート | `CLAUDE.local.md` | ローカル専用 |
| 3 | 親ディレクトリ | `CLAUDE.md` | モノレポ対応 |
| 4 | 子ディレクトリ | `CLAUDE.md` | 必要時読み込み |
| 5 | ホームフォルダ | `~/.claude/CLAUDE.md` | 全セッション適用 |


#### 3. 🔗 ファイルインポート

```markdown
# 詳細情報
詳細は@READMEを参照
利用可能なコマンドは@package.jsonを確認

# 設計文書
アーキテクチャ: @docs/architecture.md
API仕様: @docs/api-spec.md
```

> 📝 **注意**: 最大5階層までの再帰的インポートが可能

#### 4. 🔄 継続的改善

- 📝 生きているドキュメントとして管理
- 🧪 新指示追加 → 結果観察 → 改良のサイクル
- 📅 定期的なレビューとリファクタリング
- 🔍 Anthropicのプロンプト改善ツール活用

#### 5. 🗂️ 構造化のコツ

- 📑 論理的なMarkdown見出し構造
- ⚠️ 重要事項は「**IMPORTANT**」「**YOU MUST**」で強調
- 🏷️ 一貫したセクション分け

---

## 💡 プロのヒント

### 効率化テクニック

1. **🧹 頻繁な`/clear`** → 新タスク開始時に履歴クリア
2. **🎯 Plan Mode活用** → 複雑タスクは戦略的計画から開始
3. **📷 画像操作** → Control+Vで画像貼り付け

### 🎨 ワークフロー最適化

```mermaid
graph LR
    A[新タスク] --> B[/clear実行]
    B --> C[Plan Mode起動]
    C --> D[実装開始]
    D --> E[#で指示追加]
    E --> F[タスク完了]
```

---

## 📚 参考資料

| リソース | URL |
|----------|-----|
| 🏠 公式ドキュメント | [docs.claude.com](https://docs.claude.com/en/docs/claude-code/cli-reference) |
| 💻 GitHubリポジトリ | [anthropics/claude-code](https://github.com/anthropics/claude-code) |
| 📖 ベストプラクティス | [Anthropic Blog](https://www.anthropic.com/engineering/claude-code-best-practices) |

---
