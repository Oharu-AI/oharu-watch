# OHARU WATCH MVP 開発指示書

## 目的

自分が興味のあるニュースだけを自動収集し、ホームページを開くだけで読めるニュースダッシュボードを作成する。

ニュースサイト運営ではなく、自分専用の新聞を作ることが目的。

---

## 対象カテゴリ

### AI

OpenAI、ChatGPT、Codex、Claude、Gemini、Anthropic、Perplexity、AIエージェント

### Apple

iPhone、iPad、Mac、Apple Watch、Vision、iOS、macOS、Apple Intelligence

### 国内政治経済

税制改正、社会保険、年金、財政政策、金融政策、国内経済

### 海外政治経済

米国経済、FRB、中国経済、台湾情勢、半導体、世界経済

---

## MVPで実装する機能

### 1. ニュース取得

RSSと公式ブログから記事情報を取得する。

最初はRSS中心で実装する。

Reddit、Hacker News、YouTube、XはMVPでは実装しない。

### 2. サムネイル画像取得

記事URLからOGP画像、つまり og:image を取得し、サムネイルとして使用する。

og:image が取得できない場合は、カテゴリ別のデフォルト画像を表示する。

### 3. AI要約

Gemini APIを使用して、各記事について以下を生成する。

- 30秒要約
- 重要ポイント3つ
- 重要度5段階

重要度は5段階。

- ★★★★★
- ★★★★☆
- ★★★☆☆
- ★★☆☆☆
- ★☆☆☆☆

MVPでは「私への影響」は実装しない。

ただし、将来拡張用としてデータ項目だけ残す。

Gemini APIキーはGitHub Secretsに保存する。

Secrets名は `GEMINI_API_KEY` とする。

Gemini API呼び出し部分は1ファイルに分離する。

例：`summarizer.py`

将来、OpenAI APIやClaude APIに差し替えられるように、`fetch_news.py` の中にAI処理を直書きしない。

### 4. 表示ページ

AV Watch風の見やすいニュース一覧ページを作成する。

トップページでは以下を表示する。

- サムネイル画像
- カテゴリ
- タイトル
- 短い要約
- 重要度
- 続きを読むリンク

記事をクリックすると詳細表示に遷移する。

詳細ページでは以下を表示する。

- タイトル
- サムネイル画像
- 30秒要約
- 重要ポイント3つ
- 元記事リンク

---

## デザイン方針

AV Watch風のニュースサイト型レイアウトにする。

ただし丸コピーはしない。

方針：

- 白背景
- 黒文字
- 青系リンク
- サムネイル画像付きカード
- カテゴリ見出し
- 日付表示
- スマホ対応
- PCでは2カラムまたは一覧性重視
- スマホでは1カラム

---

## 技術構成

- Python
- GitHub Actions
- Gemini API
- GitHub Pages
- JSON
- HTML
- Vanilla JavaScript
- CSS

Reactなどの大型フレームワークは使用しない。

---

## ファイル構成案

```text
.github/workflows/update.yml
fetch_news.py
summarizer.py
generate_html.py
articles.json
index.html
article.html
style.css
assets/default-ai.png
assets/default-apple.png
assets/default-japan-economy.png
assets/default-world-economy.png
README.md
```

---

## データ構造

articles.json に処理済み記事を保存する。

例：

```json
{
  "id": "",
  "title": "",
  "category": "",
  "source": "",
  "published_at": "",
  "url": "",
  "thumbnail_url": "",
  "summary": "",
  "key_points": [],
  "importance": 0,
  "impact_for_me": ""
}
```

impact_for_me は将来拡張用。MVPでは空欄でよい。

---

## 記事保持期間

articles.json は直近7日分の記事のみ保持する。

7日より古い記事は自動削除する。

---

## 自動更新

GitHub Actionsで毎朝1回自動更新する。

日本時間 毎朝6時に更新。

GitHub ActionsのcronはUTC基準なので、設定は以下とする。

```yaml
cron: "0 21 * * *"
```

ニュース更新後、以下の流れをGitHub Actionsで自動化する。

1. articles.json更新
2. HTML再生成
3. GitHub Pagesへ反映

---

## 公開方法

MVPの公開先はGitHub Pagesとする。

GitHub Pagesのみで動作する構成にする。

外部サーバーは使用しない。

MVPでは以下を使用しない。

- Vercel
- Netlify
- Cloudflare Pages

GitHub Pages公開まで含めて実装する。

GitHub Pages有効化後、即公開可能な状態にする。

---

## APIコスト対策

Gemini APIの利用量が増えすぎないようにする。

方針：

- 1回の更新で処理する記事数に上限を設ける
- 同じURLの記事は再処理しない
- 既存記事は再要約しない
- Gemini APIエラー時は処理を停止し、既存ページを壊さない

運用上、Gemini API側で利用上限または予算アラートを設定する。

MVPでは月500円〜1,000円程度を目安に上限設定する。

---

## 有料記事への対応

日経、Bloombergなど、有料記事や本文が取得できない記事は、RSSで取得できるタイトル・概要のみを使って要約する。

本文全文の取得はMVPでは行わない。

---

## 開発方針

最優先は完成すること。

最初から高機能化しない。

MVPでは以下を除外する。

- 私への影響
- 個人最適化
- Reddit連携
- Hacker News連携
- YouTube連携
- X連携
- LINE通知
- メール配信
- Apple Watch通知
- Googleカレンダー連携
- 税理士試験進捗連携

---

## 完成条件

以下を満たせばMVP完成とする。

1. GitHub Actionsで毎朝6時に自動更新される
2. RSSからニュース記事を取得できる
3. OGP画像を取得してサムネイル表示できる
4. 画像がない場合はカテゴリ別デフォルト画像を表示できる
5. Gemini APIで要約・重要ポイント・重要度を生成できる
6. articles.json に記事データが保存される
7. 直近7日分の記事のみ保持される
8. index.html でニュース一覧が表示される
9. 記事クリックで詳細ページを表示できる
10. スマホで読みやすい表示になっている
