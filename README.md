# OHARU WATCH

興味のあるニュースだけを自動収集し、GitHub Pagesで読める個人用ニュースダッシュボードです。

## できること

- RSSからAI、Apple、国内政治経済、海外政治経済のニュースを取得
- 記事URLからOGP画像を取得
- 画像がない場合はカテゴリ別デフォルト画像を表示
- Gemini APIで30秒要約、重要ポイント3つ、重要度5段階を生成
- 直近7日分の記事だけを `articles.json` に保持
- `index.html` と `article.html` をGitHub Pages向けに生成
- GitHub Actionsで日本時間毎朝6時に自動更新

## GitHub Secrets

GitHubリポジトリの Secrets に以下を登録してください。

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

実際にニュース取得とGemini要約まで動かす場合は、環境変数を設定してから実行します。

```bash
GEMINI_API_KEY="your-api-key" python3 fetch_news.py
python3 generate_html.py
```

APIキーなしで表示確認だけしたい場合は、プレースホルダー要約を使えます。

```bash
python3 fetch_news.py --allow-placeholder-summary
python3 generate_html.py
```
