# ChatClipper

[![License](https://img.shields.io/badge/license-MIT-yellow)](../LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-0078D6)](https://www.microsoft.com/windows)

**日本語** · [English](../README.md) · [Русский](README-ru.md) · [Deutsch](README-de.md) · [Español](README-es.md)

Chrome で左クリックした後（Web チャットの「コピー」ボタン、例：DeepSeek）の
クリップボードを監視し、選択したプロジェクトの .docx / .md / .txt ファイルに
テキストを追記するデスクトップ ユーティリティです。
Windows で動作します。Linux / WSL / macOS のサポートは実験的です。

---

## 📋 概要

ChatClipper は、AI アシスタント（DeepSeek、ChatGPT など）とのチャットを
1 つのプロジェクト ファイルに自動保存する軽量ユーティリティです。
手動のコピー＆ペーストはもう不要です。プログラムが代わりに行います。

- クリップボードを監視し、Web チャットの「コピー」を検出します。
- コピーされたテキストをプロジェクト ファイル（.docx / .md / .txt）に追記します。
- 複数のプロジェクトを 1 つのメイン プロジェクトでサポートします。
- バックグラウンドで動作し、システム トレイに常駐します。

---

## ✨ 機能

- Chrome での左クリックによるクリップボード監視
- プロジェクト ファイルへのテキスト追記：docx、md、txt
- Markdown 解析（mistune）：見出し、太字、斜体、インライン コード、
  コード ブロック、リスト、引用、表
- オプションの Pandoc コンバーター（失敗時は mistune にフォールバック）
- 各ブロックの前にタイムスタンプと区切り線
- 複数プロジェクトと 1 つのメイン プロジェクト。形式はプロジェクトごと
- プロジェクト選択用ポップアップ ウィンドウ（不透明度と表示時間を設定可能）
- ポップアップで非メイン プロジェクトをクリックすると、通知なしでそれをメインにします
- 起動時ステータス ポップアップ。一時停止時は PAUSE スタンプ
- CRC32 リングによる重複抑制（直近 5 件）
- 最後の書き込みを元に戻す：元の .docx から削除し、別のプロジェクトへ移動します。
  undo_max_text_len と skip_secrets を尊重します
- .docx のバッファ付き書き込み：5 秒ごと、または終了時にフラッシュ
- 対象ファイルがビジーなときの保留キュー
- 内容損失チェック（loss_threshold_pct + loss_min_abs_chars）
- IPC：Windows では名前付きパイプ、POSIX では Unix ソケット、トークン認証付き
- トレイ アイコン（Windows）または Tk コントロール パネル（Linux / WSL / macOS）
- 自動起動（既定ではオフ）
- トレイ有効（既定ではオフ、Windows のみ）
- 単一インスタンス ガード（ミューテックス / ファイル ロック）
- i18n：英語、ロシア語、ドイツ語、スペイン語、日本語
- 初回起動時に OS ロケールから自動検出
- 新しい言語を追加するには `"lang.name"` を含む `locales/<code>.json` を置くだけ
- ウィンドウ アイコン：chatclipper-light.ico

---

## ⚙️ 要件
- Windows 10/11（Linux / macOS — 実験的）
- Python 3.10+
- .docx を編集するための LibreOffice または MS Word
- クリップボード ソースとしての Chrome
- オプション：Markdown → docx 用の Pandoc（PATH 内）
---

## 🚀 インストール

### 推奨：uv 仮想環境
```
    git clone https://github.com/vldbkov/chat-clipper.git
    cd chat-clipper
    uv venv
    uv pip install -r requirements.txt
    uv run python main.py
```
### 代替：pip
```
    git clone https://github.com/vldbkov/chat-clipper.git
    cd chat-clipper
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py
```
### エンド ユーザーに最も簡単：Windows インストーラー

最新リリースから `chatclipper-setup.exe` をダウンロードして実行します。
Python のインストールは不要です。
インストール後、トレイ アイコンが表示されます（Windows）。

---

## 🎮 使い方

1. ChatClipper のトレイ アイコンをクリック → **設定**。
2. プロジェクトを追加：名前、フォルダー、ファイル名。例：「DeepSeek」→「deepseek-chat.docx」。
3. 1 つのプロジェクトをメインに設定 — 書き込みは既定でそこへ行われます。
4. AI とのチャットを開き、返信をコピーします（Ctrl+C または「コピー」ボタン）。
5. ChatClipper がテキストをファイルに追記します。Word で開いて結果を確認してください。

---

## 📁 プロジェクト構成
```
    main.py                  — エントリ ポイント、トレイか GUI モードを選択
    app_state.py             — 共有 AppState、単一インスタンス
    tray_process.py          — トレイ（pystray）、メニュー、ハンドラー
    gui_process.py           — Tk メインループ、マウス フック、IPC サーバー
    control_panel.py         — トレイの代わりの Tk コントロール パネル
    actions.py               — IPC アクション レジストリ（ACTIONS 辞書）
    ipc_server.py            — IPC サーバー（パイプ/ソケット、トークン）
    ipc_client.py            — IPC クライアント
    config.py                — Project、AppConfig、config.json
    logger.py                — ログ + SafeStream
    single_instance.py       — ミューテックス / fcntl
    autostart.py             — レジストリ / .desktop / plist
    platform_utils.py        — OS ラッパー（クリップボード、アクティブ ウィンドウ、pandoc）
    clipboard.py             — platform_utils のラッパー
    mouse_hook.py            — pynput、ソース ファクトリ、クリック ウィンドウ
    hashes.py                — CRC32 リング、hashes.json
    docx_writer.py           — バッファ付きライター、スタンプ、保留キュー
    markdown_to_docx.py      — mistune AST -> python-docx
    html_to_docx.py          — html4docx（ほとんど使用されない）
    undo.py                  — remember / undo_last、last_buffers.json
    project_service.py       — write_to_project の単一エントリ ポイント
    writers/                 — writer_base、writer_docx、writer_md、
                               writer_txt、writer_factory
    sources/                 — source_base、source_chrome、
                               source_desktop_chat、source_factory
    gui_settings.py          — SettingsWindow、ProjectDialog
    gui_popup.py             — PopupWindow（選択 / ステータス）
    gui_undo.py              — UndoDialog
    ui_helpers.py            — center_window、ドラッグ ヘルパー、apply_icon
    i18n.py                  — t(key)、init、set_locale、list_languages
    locales/                 — en.json、ru.json、de.json、es.json、ja.json
    pytest.ini               — testpaths = tests
    tests/                   — コア層のユニット テスト
```
---

## 🗂 データ ファイル（コミットされません）
```
    config.json              — 設定とプロジェクト
    hashes.json              — 直近の CRC32 値のリング
    last_buffers.json        — 元に戻すための最後 / 前回の書き込み
    logging/                 — chatclipper.log（ローテーション）
    pending/                 — .docx がビジーなときにキューに入るテキスト
    ipc_token                — 共有 IPC トークン（POSIX ではモード 0600）
    chatclipper.sock         — Unix ソケット エンドポイント（POSIX のみ）
    chatclipper-light.ico    — アプリ / トレイ アイコン
```
---

## 🧩 プロジェクト構造

各プロジェクトには名前、フォルダー、ファイル名、形式
（docx / md / txt）があります。既定のファイル名は `<ProjectName>-chat.<fmt>` です。
1 つのプロジェクトがメインで、書き込みは既定でそこへ行われます。
メイン プロジェクトはポップアップ、ステータス ポップアップ、または設定ウィンドウから切り替えられます。

---

## ⚠️ 重要：バッファ付き書き込み

コピー後、対象ファイルはすぐには更新されません。変更はバッファされ、
約 5 秒ごと、またはアプリ終了時にフラッシュされます。ファイルが
Word / LibreOffice で開かれている場合、新しい内容はリアルタイムには反映されません。
閉じて再度開くと、新しいエントリを確認できます。

---

## ⚠️ 重要：.docx を手で編集しないでください

ChatClipper は最後の書き込みで追加した段落数を記憶しており、
元に戻すときはその数だけを削除します。書き込み後にファイル末尾の段落を
手動で追加、削除、変更すると、元に戻す操作はユーティリティが書いたものではなく、
数に基づいて最後の段落を削除します。
起こりうる結果：

- 手動で入れたテキストが消える — ユーティリティが自分のものとして数えます。
- ユーティリティのエントリの一部がファイルに残る。

ルール：元に戻す必要がある場合は、書き込みと元に戻すの間に .docx を触らないでください。
手で編集した場合は、元に戻すをスキップしてテキストをもう一度コピーしてください。

---

## 🌍 プラットフォーム

- **Windows 10/11** — トレイ アイコン、レジストリによる自動起動、名前付きパイプ経由の IPC。
- **Linux / WSL / macOS** — 実験的：Tk コントロール パネル、Unix ソケット経由の IPC。

---

## 🌐 新しい言語の追加

1. `locales/en.json` と同じキーを持つ `locales/<code>.json` を作成します。
2. `"lang.name": "<NativeName>"` を含めます — 設定のドロップダウンと
   OS ロケールの自動検出がファイルから読み取ります。
3. コードや設定の変更は不要です。
---

## 🐛 トラブルシューティング

| 問題 | 解決策 |
|---------|----------|
| テキストが保存されない | コピー時に Chrome がアクティブ ウィンドウであることを確認してください |
| ファイルが更新されない | 約 5 秒待つか、ファイルを閉じて再度開いてください（バッファ付き書き込み） |
| トレイ アイコンが見えない | Windows のトレイ設定を確認し、ChatClipper が実行中であることを確認してください |
| 元に戻すで誤ったテキストが削除された | 書き込みと元に戻すの間に .docx を手動で編集しないでください |
| 言語が検出されない | 設定で言語を手動で設定してください |

---

## 🤝 コントリビュート

- [バグを報告](https://github.com/vldbkov/chat-clipper/issues/new)
- [機能を提案](https://github.com/vldbkov/chat-clipper/issues/new)
- [GitHub でリポジトリにスターを付ける](https://github.com/vldbkov/chat-clipper) ⭐

---

## 📄 ライセンス

Copyright (©) 2026, Vladimir Baykov. [MIT License](../LICENSE) の下でライセンスされています。

---

[🌐 Back to English README](../README.md)