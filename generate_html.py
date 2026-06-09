"""Generate the static OHARU WATCH pages."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ARTICLES_PATH = Path("articles.json")
INDEX_PATH = Path("index.html")
ARTICLE_PATH = Path("article.html")
JST = ZoneInfo("Asia/Tokyo")
CATEGORIES = ["AI", "Apple", "国内政治経済", "海外政治経済"]


def main() -> int:
    articles = load_articles()
    INDEX_PATH.write_text(clean_output(render_index(articles)), encoding="utf-8")
    ARTICLE_PATH.write_text(clean_output(render_article_page(articles)), encoding="utf-8")
    print(f"Generated {INDEX_PATH} and {ARTICLE_PATH} with {len(articles)} articles.")
    return 0


def clean_output(markup: str) -> str:
    return "\n".join(line.rstrip() for line in markup.splitlines()) + "\n"


def load_articles() -> list[dict[str, Any]]:
    if not ARTICLES_PATH.exists():
        return []
    data = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return sorted(data, key=lambda article: parse_datetime(article.get("published_at", "")), reverse=True)


def render_index(articles: list[dict[str, Any]]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for article in articles:
        grouped[article.get("category", "その他")].append(article)

    updated_at = datetime.now(JST).strftime("%Y.%m.%d %H:%M")
    total_count = len(articles)
    lead_article = articles[0] if articles else None
    remaining_articles = articles[1:] if articles else []

    category_sections = "\n".join(
        render_category_section(category, grouped.get(category, [])) for category in CATEGORIES
    )
    latest_list = "\n".join(render_list_item(article) for article in remaining_articles[:12])

    if not articles:
        main_content = """
        <section class="empty-state">
          <h2>記事はまだありません</h2>
          <p>GitHub Actionsの初回更新が完了すると、ここにOHARU WATCHの記事が並びます。</p>
        </section>
        """
    else:
        main_content = f"""
        <section class="lead-section">
          {render_lead_article(lead_article)}
        </section>
        <section class="latest-section">
          <div class="section-heading">
            <h2>最新ニュース</h2>
            <span>{total_count}件</span>
          </div>
          <div class="article-list">
            {latest_list}
          </div>
        </section>
        {category_sections}
        """

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OHARU WATCH</title>
  <meta name="description" content="興味のあるニュースだけを自動収集する個人用ニュースダッシュボード">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a class="site-title" href="index.html">OHARU WATCH</a>
      <nav class="category-nav" aria-label="カテゴリ">
        <a href="#ai">AI</a>
        <a href="#apple">Apple</a>
        <a href="#japan-economy">国内政治経済</a>
        <a href="#world-economy">海外政治経済</a>
      </nav>
    </div>
  </header>

  <main class="page-shell">
    <div class="content-column">
      <div class="page-kicker">
        <span>Personal News Dashboard</span>
        <time datetime="{datetime.now(timezone.utc).isoformat()}">更新 {escape(updated_at)}</time>
      </div>
      {main_content}
    </div>
    <aside class="side-column" aria-label="サイドバー">
      <section class="side-panel">
        <h2>カテゴリ</h2>
        {render_category_counts(grouped)}
      </section>
      <section class="side-panel">
        <h2>重要ニュース</h2>
        {render_important_links(articles)}
      </section>
    </aside>
  </main>
</body>
</html>
"""


def render_lead_article(article: dict[str, Any] | None) -> str:
    if article is None:
        return ""
    return f"""
    <article class="lead-card">
      <a class="lead-image-link" href="article.html?id={escape(article.get('id', ''))}">
        <img src="{escape(article.get('thumbnail_url', ''))}" alt="">
      </a>
      <div class="lead-body">
        <div class="meta-row">
          <span class="category-label">{escape(article.get('category', ''))}</span>
          <time>{escape(format_date(article.get('published_at', '')))}</time>
        </div>
        <h1><a href="article.html?id={escape(article.get('id', ''))}">{escape(article.get('title', ''))}</a></h1>
        <p>{escape(article.get('summary', ''))}</p>
        <div class="card-footer">
          <span class="importance" aria-label="重要度 {escape(str(article.get('importance', 0)))}">{stars(article.get('importance', 0))}</span>
          <a class="read-more" href="article.html?id={escape(article.get('id', ''))}">続きを読む</a>
        </div>
      </div>
    </article>
    """


def render_list_item(article: dict[str, Any]) -> str:
    return f"""
    <article class="article-card">
      <a class="thumb-link" href="article.html?id={escape(article.get('id', ''))}">
        <img src="{escape(article.get('thumbnail_url', ''))}" alt="">
      </a>
      <div class="article-body">
        <div class="meta-row">
          <span class="category-label">{escape(article.get('category', ''))}</span>
          <time>{escape(format_date(article.get('published_at', '')))}</time>
        </div>
        <h3><a href="article.html?id={escape(article.get('id', ''))}">{escape(article.get('title', ''))}</a></h3>
        <p>{escape(article.get('summary', ''))}</p>
        <div class="card-footer">
          <span class="importance">{stars(article.get('importance', 0))}</span>
          <a class="read-more" href="article.html?id={escape(article.get('id', ''))}">続きを読む</a>
        </div>
      </div>
    </article>
    """


def render_category_section(category: str, articles: list[dict[str, Any]]) -> str:
    anchor = category_anchor(category)
    items = "\n".join(render_list_item(article) for article in articles[:5])
    if not items:
        items = '<p class="muted">このカテゴリの記事はまだありません。</p>'
    return f"""
    <section class="category-section" id="{anchor}">
      <div class="section-heading">
        <h2>{escape(category)}</h2>
        <span>{len(articles)}件</span>
      </div>
      <div class="article-list compact-list">
        {items}
      </div>
    </section>
    """


def render_category_counts(grouped: dict[str, list[dict[str, Any]]]) -> str:
    links = []
    for category in CATEGORIES:
        links.append(
            f'<a class="side-link" href="#{category_anchor(category)}"><span>{escape(category)}</span><strong>{len(grouped.get(category, []))}</strong></a>'
        )
    return "\n".join(links)


def render_important_links(articles: list[dict[str, Any]]) -> str:
    important = sorted(
        articles,
        key=lambda article: (int(article.get("importance", 0) or 0), parse_datetime(article.get("published_at", ""))),
        reverse=True,
    )[:5]
    if not important:
        return '<p class="muted">重要ニュースはまだありません。</p>'
    return "\n".join(
        f'<a class="important-link" href="article.html?id={escape(article.get("id", ""))}"><span>{stars(article.get("importance", 0))}</span>{escape(article.get("title", ""))}</a>'
        for article in important
    )


def render_article_page(articles: list[dict[str, Any]]) -> str:
    embedded_articles = json.dumps(articles, ensure_ascii=False).replace("</", "<\\/")
    return """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>記事詳細 - OHARU WATCH</title>
  <meta name="description" content="OHARU WATCHの記事詳細">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a class="site-title" href="index.html">OHARU WATCH</a>
      <nav class="category-nav" aria-label="カテゴリ">
        <a href="index.html#ai">AI</a>
        <a href="index.html#apple">Apple</a>
        <a href="index.html#japan-economy">国内政治経済</a>
        <a href="index.html#world-economy">海外政治経済</a>
      </nav>
    </div>
  </header>

  <main class="detail-shell">
    <article class="detail-article" id="article-root">
      <p class="muted">記事を読み込んでいます。</p>
    </article>
  </main>

  <script id="articles-data" type="application/json">__ARTICLES_JSON__</script>
  <script>
    const defaultImages = {
      "AI": "assets/default-ai.png",
      "Apple": "assets/default-apple.png",
      "国内政治経済": "assets/default-japan-economy.png",
      "海外政治経済": "assets/default-world-economy.png"
    };

    const params = new URLSearchParams(window.location.search);
    const articleId = params.get("id");
    const root = document.getElementById("article-root");
    const articles = JSON.parse(document.getElementById("articles-data").textContent);

    const article = articles.find((item) => item.id === articleId);
    if (article) {
      renderArticle(article);
    } else {
      renderMissing();
    }

    function renderArticle(article) {
      document.title = `${article.title} - OHARU WATCH`;
      root.replaceChildren();

      const back = createLink("index.html", "一覧に戻る", "back-link");
      root.appendChild(back);

      const meta = el("div", "meta-row");
      meta.appendChild(el("span", "category-label", article.category || ""));
      meta.appendChild(el("time", "", formatDate(article.published_at)));
      root.appendChild(meta);

      root.appendChild(el("h1", "detail-title", article.title || ""));

      const image = document.createElement("img");
      image.className = "detail-image";
      image.src = article.thumbnail_url || defaultImages[article.category] || "";
      image.alt = "";
      root.appendChild(image);

      const summaryBlock = el("section", "detail-block");
      summaryBlock.appendChild(el("h2", "", "詳しめ要約"));
      summaryBlock.appendChild(el("p", "", article.summary || ""));
      summaryBlock.appendChild(createLink(article.url, "元記事を読む", "source-link"));
      root.appendChild(summaryBlock);

      const pointsBlock = el("section", "detail-block");
      pointsBlock.appendChild(el("h2", "", "重要ポイント"));
      const list = document.createElement("ul");
      list.className = "point-list";
      (article.key_points || []).slice(0, 3).forEach((point) => {
        list.appendChild(el("li", "", point));
      });
      pointsBlock.appendChild(list);
      root.appendChild(pointsBlock);

      const footer = el("div", "detail-footer");
      footer.appendChild(el("span", "importance", stars(article.importance)));
      footer.appendChild(createLink(article.url, "元記事を読む", "source-link"));
      root.appendChild(footer);
    }

    function renderMissing() {
      root.replaceChildren();
      root.appendChild(createLink("index.html", "一覧に戻る", "back-link"));
      root.appendChild(el("h1", "detail-title", "記事が見つかりません"));
      root.appendChild(el("p", "muted", "一覧ページからもう一度記事を選んでください。"));
    }

    function el(tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }

    function createLink(href, text, className) {
      const link = document.createElement("a");
      link.href = href;
      link.textContent = text;
      if (className) link.className = className;
      if (href && href.startsWith("http")) {
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
      return link;
    }

    function stars(value) {
      const count = Math.max(1, Math.min(5, Number(value) || 1));
      return "★".repeat(count) + "☆".repeat(5 - count);
    }

    function formatDate(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "";
      return new Intl.DateTimeFormat("ja-JP", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      }).format(date);
    }
  </script>
</body>
</html>
""".replace("__ARTICLES_JSON__", embedded_articles)


def stars(value: Any) -> str:
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 1
    count = max(1, min(5, count))
    return "★" * count + "☆" * (5 - count)


def category_anchor(category: str) -> str:
    return {
        "AI": "ai",
        "Apple": "apple",
        "国内政治経済": "japan-economy",
        "海外政治経済": "world-economy",
    }.get(category, "other")


def format_date(value: str) -> str:
    date = parse_datetime(value).astimezone(JST)
    return date.strftime("%Y.%m.%d %H:%M")


def parse_datetime(value: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    try:
        date = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc)


if __name__ == "__main__":
    raise SystemExit(main())
