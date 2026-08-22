# OHARU WATCH

興味のあるニュースだけを自動収集し、GitHub Pagesで読める個人用ニュースダッシュボードです。

詳しい経緯・運用メモは [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md) を参照してください。

## できること

- RSS / Google News RSS / 公式ブログRSSから、次の順でニュースを取得
  1. **AI最新情報（国内）**
  2. **AI最新情報（国外）**
  3. **Apple（最新公式）**
  4. **Apple（リーク情報）**
- 国内AIはITmedia AI+、AIsmiley、AINOW、Publickey、Impress Watch、国内AI企業の公式発信とGoogleニュースを横断して収集
- RedditのAI系人気スレッドも、複数サブレディットを1回のRSS取得にまとめて収集
- 通常はカテゴリ別デフォルト画像を表示し、元記事ページのOGP画像取得は必要時だけ有効化
- 日本語記事は元記事の本文を抜粋、英語記事はタイトル・本文を**無料のGoogle翻訳**で日本語化
- 翻訳タイトルは、企業名・製品名・数値を保ちながら、専門用語を非エンジニアにも分かるニュース見出しへ整形
- 記事は「本文抜粋＋元記事リンク」方式で表示（要約の言い換えや星評価はしない）
- 「おすすめ」掲載の記事は通常記事から除外し、同じ記事を二重表示しない
- 通常記事はカテゴリごとに最大100件を用意し、最初の30件から20件ずつ追加表示
- 直近7日分の記事だけを `articles.json` に保持
- `index.html` と `article.html` をGitHub Pages向けに生成
- GitHub Actionsで日本時間毎朝6時に自動更新

### Gemini APIについて（既定オフ）

`summarizer.py` にGemini要約のロジックは残していますが、**既定では使いません**
（`USE_GEMINI_SUMMARY=0` が既定値）。無料翻訳＋本文抜粋方式に切り替えたため、
通常運用では **GEMINI_API_KEYは不要**です。

Gemini要約を復活させたい場合のみ、GitHub Secretsに以下を登録し、
実行時に `USE_GEMINI_SUMMARY=1` を指定してください。

```text
GEMINI_API_KEY
```

## 公開方法

公開先はGitHub Pagesのみです。Vercel、Netlify、Cloudflare Pagesなどの外部ホスティングは使いません。

GitHub PagesのSourceは `GitHub Actions` を選択してください。有効化後は、`.github/workflows/update.yml` が以下を自動で行います。

1. `articles.json` を更新
2. `index.html` と `article.html` を再生成
3. GitHub Pagesへ反映

## ローカル確認

```bash
python3 generate_html.py
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000` を開くと確認できます。

ニュース取得（無料・APIキー不要、既定の動き）:

```bash
python3 fetch_news.py
python3 generate_html.py
```

通常はRSSに含まれる本文を使うため、更新を安定して完走できます。元記事ページから本文・画像を追加取得したい場合だけ、次のように指定します（更新時間と失敗しやすさは増えます）。

```bash
FETCH_ARTICLE_PAGES=1 python3 fetch_news.py
```

Redditを一時停止したい場合だけ、次のように指定します。

```bash
ENABLE_REDDIT=0 python3 fetch_news.py
```

Gemini要約を試したい場合のみ:

```bash
USE_GEMINI_SUMMARY=1 GEMINI_API_KEY="your-api-key" python3 fetch_news.py
python3 generate_html.py
```

## 構文チェック

```bash
PYTHONPYCACHEPREFIX=/private/tmp/oharu-watch-pycache python3 -m py_compile fetch_news.py summarizer.py generate_html.py
```

通常の `python3 -m py_compile ...` はmacOSのユーザーキャッシュ書き込み権限で失敗することがあるため、上のように一時ディレクトリを指定します。
