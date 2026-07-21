# OHARU WATCH 作業引き継ぎ

最終更新: 2026-07-22（Codex）

## 目的

GitHub Pagesで公開する個人用ニュースダッシュボード。無料のRSS取得・本文抜粋・必要時のGoogle翻訳を基本とし、Gemini要約は既定で停止している。

## 現在の状態

- 表示・取得カテゴリは優先順に、`AI最新情報（国内）`、`AI最新情報（国外）`、`Apple（最新公式）`、`Apple（リーク情報）` の4つ。
- 国内AIの情報源をITmedia AI+、AIsmiley、AINOW、Publickey、Impress Watch、国内AI企業の公式発信、Googleニュース横断検索へ拡張した。
- Redditは `r/OpenAI`、`r/ClaudeAI`、`r/LocalLLaMA`、`r/singularity`、`r/Anthropic` を1本の人気順RSSとして取得する。Reddit本文はフィード内の内容を使い、投稿ページへ再アクセスしない。
- おすすめ5件は通常記事から除外するため、トップページで同じ記事は二重に表示されない。
- 直近7日分だけを保持する。通常の記事は各カテゴリ最大100件まで用意し、最初は30件、以後20件ずつ追加表示する。
- 画面は白・ネイビー・ブルーを基調に、余白、カード、カテゴリ色、固定ヘッダー、スマホ用横スクロールナビを統一したニュースメディア調のデザイン。
- 通常更新はRSS本文のみを使うため、元ページ取得による長時間処理を避ける。`FETCH_ARTICLE_PAGES=1` を指定したときだけ元ページの画像・本文を取得する。

## 今回の変更

- `fetch_news.py`: 4カテゴリ化、国内AI情報源追加、カテゴリの最低1件確保、同一タイトルの重複除去、Reddit有効化、元記事ページ取得の既定停止。
- `generate_html.py`: 4カテゴリ表示、ナビゲーション更新、おすすめと通常記事の表示重複を解消、カテゴリごとの表示上限を100件に拡大し、20件ずつの追加表示を実装。
- `style.css`: PC・スマホ共通のデザインシステムへ刷新。失敗した外部画像の既定画像への切り替えと、文字化け本文の表示保護も追加。
- `README.md` とGitHub Actions設定を現行運用へ更新。
- `articles.json` は実取得済み。2026-07-22時点で295件あり、表示上は国内AI 68件・国外AI 169件・Apple公式 1件・Appleリーク 57件。

## 検証結果

- `PYTHONPYCACHEPREFIX=/private/tmp/oharu-watch-pycache python3 -m py_compile fetch_news.py summarizer.py generate_html.py` は成功。
- Redditを含む実行で、Reddit RSSから4件を取得し、最大5件の新規記事を保存できた。
- `python3 generate_html.py` は295件で成功。
- 表示用データで、おすすめと通常記事の重複は0件、記事タイトル重複は0件を確認。
- ブラウザ実測で、国内AIは30件から50件へ追加表示され、残り15件の表示案内へ変わることを確認。
- 1280pxとスマホ相当375pxの両方で横はみ出し0、一覧・記事詳細の表示を目視確認。

## 未解決事項

- `iPhone Mania` はローカルのPython 3.9ではTLSエラーになる。ほかのApple情報源とGoogleニュースで更新は継続できる。
- `Impress Watch` と`Microsoft AI`は取得自体は成功するが、直近フィードではカテゴリ条件に一致する記事が0件だった。

## 次の作業

1. 次回の定期更新後も追加表示ボタンとカテゴリ件数が維持されることを確認する。
2. Apple公式の記事量を数日観察し、少なければApple公式の追加RSSを検討する。
3. 失敗している情報源は、RSS URLの変更を確認できた場合だけ修正する。

## 再開時のコマンド

```bash
git status --short
PYTHONPYCACHEPREFIX=/private/tmp/oharu-watch-pycache python3 -m py_compile fetch_news.py summarizer.py generate_html.py
python3 fetch_news.py
python3 generate_html.py
```
