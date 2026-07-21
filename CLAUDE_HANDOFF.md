# OHARU WATCH Claude 引き継ぎ資料

作成日: 2026-06-22  
想定引き継ぎ日: 2026-06-24  
前提: 2026-06-23で有料ChatGPT運用をいったん終了し、以後Claudeでこのプロジェクトを継続する。

## Claudeへの最初の依頼文

Claudeで作業を再開するときは、まず以下をそのまま渡す。

```text
このプロジェクトは個人用ニュースダッシュボード「OHARU WATCH」です。
最初に CLAUDE_HANDOFF.md、README.md、AI Inbox/HANDOFF/Instructions/oharu-watch-mvp-development-instructions.md を読んで、現在の仕様・構成・未完了点を把握してください。

作業では次の方針を守ってください。
- GitHub Pagesだけで公開する静的サイトとして維持する
- Python、JSON、HTML、Vanilla JavaScript、CSSだけで進める
- Reactなどの大型フレームワークは追加しない
- Gemini API呼び出しは summarizer.py に分離したままにする
- fetch_news.py にAI API処理を直書きしない
- articles.json は直近7日分の記事だけを保持する
- 未コミット変更がある場合は勝手に戻さず、内容を確認してから作業する
```

## プロジェクト概要

OHARU WATCHは、自分が興味のあるニュースだけを自動収集し、GitHub Pagesで読める個人用ニュースダッシュボード。

現在の主な対象カテゴリは `AI` と `Apple`。過去のMVP指示書には国内政治経済・海外政治経済もあるが、現行コードでは `ACTIVE_CATEGORIES` / `CATEGORIES` が `AI` と `Apple` に絞られている。政治経済はトップページからYahoo!ニュースへ誘導する設計になっている。

主な機能:

- RSS / Google News RSS / 公式ブログRSSから記事取得
- 記事URLからOGP画像を取得
- OGP画像が取れない場合はカテゴリ別デフォルト画像を使用
- Gemini APIでタイトル翻訳、要約、記事内容、重要ポイント3つ、重要度5段階を生成
- `articles.json` に直近7日分の記事だけ保持
- `index.html` と `article.html` を生成
- GitHub Actionsで日本時間毎朝6時に更新・GitHub Pagesへデプロイ

## 現在の場所

ローカル作業ディレクトリ:

```text
/Users/oharu/haru-ai-workspace/projects/oharu-watch
```

2026-07-22に CODEX と Claude で共同開発できるよう、`/Users/oharu/プロジェクト/おはるWATCH` からこの場所へ移動した。フォルダー名は GitHub リポジトリ名（`Oharu-AI/oharu-watch`）と揃え、日本語・濁点合成文字によるパスの不具合を避けるため ASCII の `oharu-watch` にしている。Git 履歴・リモート設定はそのまま引き継いでいる。

`CODEX_PROJECT_MOVED_NOTICE.md` に移動の経緯を記載。旧場所 `/Users/oharu/プロジェクト/おはるWATCH` には移転案内スタブだけを残してある。

## 重要ファイル

```text
README.md
  現在の公開方法、実行方法、GitHub Secretsなどの基本説明。

AI Inbox/HANDOFF/Instructions/oharu-watch-mvp-development-instructions.md
  MVPの元仕様。Claudeは最初に読むこと。

fetch_news.py
  RSS取得、記事選別、OGP画像取得、articles.json更新の中心。

summarizer.py
  Gemini APIで要約を作る層。将来Claude APIやOpenAI APIへ差し替えるならここを中心に変更する。

generate_html.py
  articles.jsonからindex.htmlとarticle.htmlを生成する。

articles.json
  処理済み記事データ。直近7日分のみ保持。

index.html
  一覧ページ。generate_html.pyの出力。

article.html
  詳細ページ。generate_html.pyの出力。

style.css
  AV Watch風の静的サイトデザイン。

.github/workflows/update.yml
  GitHub Actions。日本時間毎朝6時更新、GitHub Pagesデプロイ。

assets/
  カテゴリ別デフォルト画像。
```

## 実行方法

表示用HTMLだけ再生成:

```bash
python3 generate_html.py
```

ローカルで表示確認:

```bash
python3 -m http.server 8000
```

ブラウザで開く:

```text
http://localhost:8000
```

ニュース取得とGemini要約まで実行:

```bash
GEMINI_API_KEY="your-api-key" python3 fetch_news.py
python3 generate_html.py
```

APIキーなしでプレースホルダー要約を許可:

```bash
python3 fetch_news.py --allow-placeholder-summary
python3 generate_html.py
```

Python構文チェック:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/oharu-watch-pycache python3 -m py_compile fetch_news.py summarizer.py generate_html.py
```

通常の `python3 -m py_compile ...` はmacOSのユーザーキャッシュ書き込み権限で失敗することがあるため、上のように一時ディレクトリを指定する。

## GitHub Actions / 公開

公開先はGitHub Pagesのみ。Vercel、Netlify、Cloudflare Pagesは使わない。

必要なGitHub Secret:

```text
GEMINI_API_KEY
```

`.github/workflows/update.yml` の流れ:

1. push時またはスケジュール時に起動
2. スケジュール・手動実行では `python fetch_news.py` で記事更新
3. `python generate_html.py` でHTML生成
4. スケジュール・手動実行では更新ファイルをコミットしてpush
5. `_site` に静的ファイルを集める
6. GitHub Pagesへデプロイ

スケジュール:

```yaml
cron: "0 21 * * *"
```

これはUTC 21:00、つまり日本時間の毎朝6:00。

## 現在の実装メモ

### fetch_news.py

- `RETENTION_DAYS = 7`
- 1回で処理する新規記事数は環境変数で調整可能
  - `MAX_NEW_ARTICLES` 初期値24
  - `MAX_NEW_PER_CATEGORY` 初期値18
  - `MAX_RESUMMARIZE_ARTICLES` 初期値4
  - `MAX_TRANSLATE_EXISTING_ARTICLES` 初期値20
- 現行アクティブカテゴリは `AI` と `Apple`
- `deepmind` を含む記事は除外
- AIカテゴリのうち、OpenAI / ChatGPT / Anthropic / Claude / Google AIなどに関係する記事をGemini要約対象にしている
- Geminiが429などで詰まった場合、その実行中はGemini要約を止めてRSS fallbackに切り替える

### summarizer.py

- Gemini endpointを直接HTTPで呼び出している
- デフォルトモデルは `gemini-2.5-flash-lite`
- fallback modelに `gemini-2.5-flash-lite` と `gemini-2.5-flash`
- 出力はJSONのみを要求
- 返却データは以下に正規化される
  - `title`
  - `summary`
  - `article_body`
  - `key_points`
  - `importance`
  - `source`

### generate_html.py

- `articles.json` を読み込んで `index.html` / `article.html` を生成
- 表示カテゴリは `AI` と `Apple`
- 一覧トップは最新記事を大きく表示
- 詳細ページは `article.html?id=...` で、埋め込みJSONから該当記事を探す

## 現在の作業状態

2026-06-22時点で、以下の未コミット変更がある。

```text
 M article.html
 M articles.json
 M fetch_news.py
 M index.html
 M summarizer.py
?? CODEX_PROJECT_MOVED_NOTICE.md
?? CLAUDE_HANDOFF.md
```

`python3 generate_html.py` 実行済み。結果:

```text
Generated index.html and article.html with 66 articles.
```

構文チェックも以下で成功済み。

```bash
PYTHONPYCACHEPREFIX=/private/tmp/oharu-watch-pycache python3 -m py_compile fetch_news.py summarizer.py generate_html.py
```

Claudeへの注意:

- 未コミット変更を勝手に戻さないこと。
- `index.html` と `article.html` は生成物なので、表示変更は基本的に `generate_html.py` と `style.css` を修正してから再生成する。
- `articles.json` は自動更新で大きく変わる。差分が大きくても異常とは限らない。

## 2026-07-22 更新状況（この節が従来の記録より新しい）

- 現在のカテゴリは、`AI最新情報（国内）`、`AI最新情報（国外）`、`Apple（最新公式）`、`Apple（リーク情報）` の優先順4分類。
- 国内AI情報源を増やし、Redditの人気スレッドも1本のRSS取得で追加済み。Redditは投稿ページへ再アクセスしないため、レート制限を避ける。
- おすすめ記事は通常記事から除外するので、一覧上の重複表示はしない。
- 更新の安定性のため、既定ではRSS本文だけを使う。元ページからの画像・本文取得は `FETCH_ARTICLE_PAGES=1` を指定した場合のみ。
- 2026-07-22に、Redditを含む実データ更新、HTML生成、構文チェックを完了した。詳細な実行結果と次の作業は `HANDOFF.md` を参照。

## データ構造

`articles.json` の各記事は概ね以下の形。

```json
{
  "id": "",
  "title": "",
  "original_title": "",
  "category": "",
  "source": "",
  "source_url": "",
  "published_at": "",
  "url": "",
  "thumbnail_url": "",
  "summary": "",
  "article_body": "",
  "key_points": [],
  "importance": 0,
  "summary_source": "",
  "impact_for_me": ""
}
```

`impact_for_me` は将来拡張用。MVPでは空欄でよい。

## 今後やるとよいこと

優先度高:

- GitHub Pagesで最新デプロイが正常に見えるか確認
- GitHub Secret `GEMINI_API_KEY` が設定されているか確認
- GitHub Actionsの直近実行が成功しているか確認
- `articles.json` の記事数やカテゴリ偏りを見て、RSSソースの質を調整

優先度中:

- 要約対象のAI記事フィルタを見直す
- Apple記事もGemini要約するか判断する
- `deepmind` 除外が本当に必要か見直す
- 記事詳細ページに元タイトル表示を追加するか検討

将来拡張:

- Claude APIやOpenAI APIへ要約プロバイダを差し替える
- 国内政治経済・海外政治経済カテゴリを復活させる
- 「私への影響」を生成する
- LINE通知、メール通知、Apple Watch通知などを追加する

## Claudeが作業するときの基本手順

1. `git status --short` で未コミット変更を確認
2. `README.md` とこのファイルを読む
3. 仕様の詳細が必要なら `AI Inbox/HANDOFF/Instructions/oharu-watch-mvp-development-instructions.md` を読む
4. コード変更は生成元を優先する
5. `python3 generate_html.py` でHTMLを再生成
6. `PYTHONPYCACHEPREFIX=/private/tmp/oharu-watch-pycache python3 -m py_compile fetch_news.py summarizer.py generate_html.py` で確認
7. 必要ならローカルサーバーで表示確認

## 大事な思想

このプロジェクトはニュースサイト運営ではなく、自分専用の新聞を作ることが目的。

最優先は、毎朝見たくなること。  
高機能化よりも、読みやすさ、安定更新、興味のあるニュースだけに絞ることを優先する。
