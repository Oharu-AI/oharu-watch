# AGENTS.md（CODEX向け）

このファイルはCODEXがこのリポジトリを開いたときに自動で読む入口です。
詳細な経緯・現在の仕様・運用ルールは重複させず、すべて
**[CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md)** に集約しています。作業前に必ず読んでください。

## 最初にやること

1. [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md) を読む（現在の仕様・構成・運用ルール）
2. [README.md](README.md) を読む（実行方法・公開方法）
3. `git status` で未コミット変更を確認する。**勝手に戻さず、内容を確認してから作業すること**

## 絶対に守ること（要約）

- GitHub Pagesだけで公開する静的サイト。React等の大型フレームワークは追加しない
- Python / JSON / HTML / Vanilla JavaScript / CSS のみで進める
- Gemini API呼び出しは `summarizer.py` に分離したまま。`fetch_news.py` にAI API処理を直書きしない
  - ただし現在Gemini要約は**既定で停止**（`USE_GEMINI_SUMMARY=0`）。通常運用は無料の本文抜粋＋翻訳方式
- `articles.json` は直近7日分の記事だけを保持する
- `index.html` と `article.html` は生成物。表示を変えるときは `generate_html.py` と `style.css` を直してから再生成する
- 未コミット変更を勝手に `git checkout` / `reset` で戻さない

## 作業ディレクトリとリモート

- 作業ディレクトリ: `/Users/oharu/haru-ai-workspace/projects/oharu-watch`
  （2026-07-22にCODEX共同開発のため `/Users/oharu/プロジェクト/おはるWATCH` から移動。経緯は [CODEX_PROJECT_MOVED_NOTICE.md](CODEX_PROJECT_MOVED_NOTICE.md)）
- リモート: `https://github.com/Oharu-AI/oharu-watch.git`（mainブランチへ直push運用、一人開発なのでPRは使わない）

## 開発者

非エンジニア寄りのユーザー。Git/GitHub用語は都度かみ砕いて説明する。
コスト（課金・APIキーの要否）を気にするので、無料で完結する変更かどうかを明示する。
