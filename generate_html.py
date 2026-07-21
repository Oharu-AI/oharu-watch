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
CATEGORIES = [
    "AI最新情報（国内）",
    "AI最新情報（国外）",
    "Apple（最新公式）",
    "Apple（リーク情報）",
]
EXCLUDED_KEYWORDS = ["deepmind"]
INITIAL_CATEGORY_ARTICLES = 30
LOAD_MORE_STEP = 20
MAX_CATEGORY_ARTICLES = 100
CATEGORY_DEFAULT_IMAGES = {
    "AI最新情報（国内）": "assets/default-ai.png",
    "AI最新情報（国外）": "assets/default-ai.png",
    "Apple（最新公式）": "assets/default-apple.png",
    "Apple（リーク情報）": "assets/default-apple.png",
}


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
    filtered_articles = []
    for article in data:
        normalized_article = dict(article)
        normalized_article["category"] = normalize_category(normalized_article)
        if normalized_article.get("category") in CATEGORIES and not contains_excluded_keyword(normalized_article):
            filtered_articles.append(normalized_article)
    return sorted(filtered_articles, key=lambda article: parse_datetime(article.get("published_at", "")), reverse=True)


def normalize_category(article: dict[str, Any]) -> str:
    """旧2カテゴリの記事を、現在の4カテゴリの表示先へ振り分ける。"""
    category = str(article.get("category", ""))
    if category in CATEGORIES:
        return category
    if category == "Apple":
        source = str(article.get("source", ""))
        url = str(article.get("url", ""))
        return "Apple（最新公式）" if source.startswith("Apple ") or "apple.com/" in url else "Apple（リーク情報）"
    if category == "AI":
        source = str(article.get("source", ""))
        url = str(article.get("url", ""))
        domestic_sources = {"AIsmiley AIニュース", "AINOW", "ITmedia AI+", "Ledge.ai", "Sakana AI", "CyberAgent AI Lab"}
        return "AI最新情報（国内）" if source in domestic_sources or ".jp" in url else "AI最新情報（国外）"
    return category


def contains_excluded_keyword(article: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(article.get(key, ""))
        for key in ["title", "description", "summary", "article_body", "source", "url"]
    ).lower()
    return any(keyword in haystack for keyword in EXCLUDED_KEYWORDS)


def render_index(articles: list[dict[str, Any]]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for article in articles:
        grouped[article.get("category", "その他")].append(article)

    updated_at = datetime.now(JST).strftime("%Y.%m.%d %H:%M")
    total_count = len(articles)
    recommended_articles = select_recommended_articles(articles)
    recommended_ids = {article.get("id") for article in recommended_articles}
    regular_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for article in articles:
        if article.get("id") not in recommended_ids:
            regular_grouped[article.get("category", "その他")].append(article)
    category_sections = "\n".join(
        render_category_section(category, regular_grouped.get(category, [])) for category in CATEGORIES
    )

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
          <div class="section-heading">
            <h2>おすすめ</h2>
            <span>最新{len(recommended_articles)}件</span>
          </div>
          {render_recommendations(recommended_articles)}
        </section>
        <section class="latest-section">
          <div class="section-heading">
            <h2>通常の記事</h2>
            <span>{total_count - len(recommended_articles)}件</span>
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
      <a class="site-title" href="index.html">OHARU <span>WATCH</span></a>
      <nav class="category-nav" aria-label="カテゴリ">
        <a href="#ai-japan">AI（国内）</a>
        <a href="#ai-global">AI（国外）</a>
        <a href="#apple-official">Apple（公式）</a>
        <a href="#apple-rumors">Apple（リーク）</a>
      </nav>
    </div>
  </header>

  <main class="page-shell">
    <div class="content-column">
      <div class="page-kicker">
        <span>CURATED INTELLIGENCE / DAILY BRIEFING</span>
        <time datetime="{datetime.now(timezone.utc).isoformat()}">更新 {escape(updated_at)}</time>
      </div>
      {main_content}
    </div>
    <aside class="side-column" aria-label="サイドバー">
      <section class="side-panel">
        <h2>カテゴリ</h2>
        {render_category_counts(grouped)}
      </section>
    </aside>
  </main>
  {render_load_more_script()}
</body>
</html>
"""


def render_lead_article(article: dict[str, Any] | None) -> str:
    if article is None:
        return ""
    return f"""
    <article class="lead-card">
      <a class="lead-image-link" href="article.html?id={escape(article.get('id', ''))}">
        <img src="{escape(article_image(article))}" data-fallback="{escape(category_default_image(article))}" alt="" decoding="async" fetchpriority="high">
      </a>
      <div class="lead-body">
        <div class="meta-row">
          <span class="category-label" data-category="{escape(article.get('category', ''))}">{escape(article.get('category', ''))}</span>
          <span class="source-name">{escape(article.get('source', ''))}</span>
          <time>{escape(format_date(article.get('published_at', '')))}</time>
        </div>
        <h1><a href="article.html?id={escape(article.get('id', ''))}">{escape(article.get('title', ''))}</a></h1>
        <p>{escape(display_summary(article))}</p>
        <div class="card-footer">
          <a class="read-more" href="article.html?id={escape(article.get('id', ''))}">続きを読む</a>
        </div>
      </div>
    </article>
    """


def select_recommended_articles(articles: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """おすすめは重要度を優先し、同点なら新しい記事を選ぶ。"""
    return sorted(
        articles,
        key=lambda article: (
            int(article.get("importance", 0) or 0),
            parse_datetime(article.get("published_at", "")),
        ),
        reverse=True,
    )[:limit]


def render_recommendations(articles: list[dict[str, Any]]) -> str:
    if not articles:
        return '<p class="muted">おすすめの記事はまだありません。</p>'
    lead = render_lead_article(articles[0])
    rest = "\n".join(render_list_item(article) for article in articles[1:])
    return f"""
    {lead}
    <div class="article-list compact-list">
      {rest}
    </div>
    """


def render_list_item(article: dict[str, Any], hidden: bool = False) -> str:
    hidden_attribute = " hidden" if hidden else ""
    image_attribute = (
        f'data-src="{escape(article_image(article))}"'
        if hidden
        else f'src="{escape(article_image(article))}"'
    )
    return f"""
    <article class="article-card"{hidden_attribute}>
      <a class="thumb-link" href="article.html?id={escape(article.get('id', ''))}">
        <img {image_attribute} data-fallback="{escape(category_default_image(article))}" alt="" loading="lazy" decoding="async">
      </a>
      <div class="article-body">
        <div class="meta-row">
          <span class="category-label" data-category="{escape(article.get('category', ''))}">{escape(article.get('category', ''))}</span>
          <span class="source-name">{escape(article.get('source', ''))}</span>
          <time>{escape(format_date(article.get('published_at', '')))}</time>
        </div>
        <h3><a href="article.html?id={escape(article.get('id', ''))}">{escape(article.get('title', ''))}</a></h3>
        <p>{escape(display_summary(article))}</p>
        <div class="card-footer">
          <a class="read-more" href="article.html?id={escape(article.get('id', ''))}">続きを読む</a>
        </div>
      </div>
    </article>
    """


def render_category_section(category: str, articles: list[dict[str, Any]]) -> str:
    anchor = category_anchor(category)
    displayed_articles = articles[:MAX_CATEGORY_ARTICLES]
    items = "\n".join(
        render_list_item(article, hidden=index >= INITIAL_CATEGORY_ARTICLES)
        for index, article in enumerate(displayed_articles)
    )
    if not items:
        items = '<p class="muted">このカテゴリの記事はまだありません。</p>'
    if len(articles) > MAX_CATEGORY_ARTICLES:
        count_label = f"{MAX_CATEGORY_ARTICLES}件表示（全{len(articles)}件）"
    else:
        count_label = f"{len(displayed_articles)}件"
    hidden_count = max(0, len(displayed_articles) - INITIAL_CATEGORY_ARTICLES)
    load_more = ""
    if hidden_count:
        next_count = min(LOAD_MORE_STEP, hidden_count)
        load_more = f"""
        <div class="load-more-wrap">
          <button class="load-more" type="button" data-target="{anchor}-list" data-step="{LOAD_MORE_STEP}" aria-controls="{anchor}-list">
            さらに{next_count}件表示
          </button>
        </div>
        """
    return f"""
    <section class="category-section" id="{anchor}">
      <div class="section-heading">
        <h2>{escape(category)}</h2>
        <span>{escape(count_label)}</span>
      </div>
      <div class="article-list compact-list" id="{anchor}-list">
        {items}
      </div>
      {load_more}
    </section>
    """


def article_image(article: dict[str, Any]) -> str:
    return str(article.get("thumbnail_url") or CATEGORY_DEFAULT_IMAGES.get(article.get("category", ""), ""))


def category_default_image(article: dict[str, Any]) -> str:
    return CATEGORY_DEFAULT_IMAGES.get(str(article.get("category", "")), "")


def display_summary(article: dict[str, Any]) -> str:
    summary = str(article.get("summary", ""))
    if summary.count("�") >= 3:
        return "本文の文字コードを確認中です。内容は元記事でご覧いただけます。"
    return summary


def render_load_more_script() -> str:
    return """
  <script>
    document.querySelectorAll("img[data-fallback]").forEach((image) => {
      image.addEventListener("error", () => {
        const fallback = image.dataset.fallback;
        if (fallback && !image.src.endsWith(fallback)) image.src = fallback;
      });
    });

    document.querySelectorAll(".load-more").forEach((button) => {
      button.addEventListener("click", () => {
        const list = document.getElementById(button.dataset.target);
        if (!list) return;
        const step = Number(button.dataset.step) || 20;
        const hiddenCards = Array.from(list.querySelectorAll(".article-card[hidden]"));
        hiddenCards.slice(0, step).forEach((card) => {
          card.querySelectorAll("img[data-src]").forEach((image) => {
            image.src = image.dataset.src;
            image.removeAttribute("data-src");
          });
          card.hidden = false;
        });
        const remaining = list.querySelectorAll(".article-card[hidden]").length;
        if (!remaining) {
          button.closest(".load-more-wrap").remove();
          return;
        }
        button.textContent = `さらに${Math.min(step, remaining)}件表示`;
      });
    });
  </script>
    """


def render_category_counts(grouped: dict[str, list[dict[str, Any]]]) -> str:
    links = []
    for category in CATEGORIES:
        links.append(
            f'<a class="side-link" href="#{category_anchor(category)}"><span>{escape(category)}</span><strong>{len(grouped.get(category, []))}</strong></a>'
        )
    return "\n".join(links)


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
      <a class="site-title" href="index.html">OHARU <span>WATCH</span></a>
      <nav class="category-nav" aria-label="カテゴリ">
        <a href="index.html#ai-japan">AI（国内）</a>
        <a href="index.html#ai-global">AI（国外）</a>
        <a href="index.html#apple-official">Apple（公式）</a>
        <a href="index.html#apple-rumors">Apple（リーク）</a>
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
      "AI最新情報（国内）": "assets/default-ai.png",
      "AI最新情報（国外）": "assets/default-ai.png",
      "Apple（最新公式）": "assets/default-apple.png",
      "Apple（リーク情報）": "assets/default-apple.png"
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
      const category = el("span", "category-label", article.category || "");
      category.dataset.category = article.category || "";
      meta.appendChild(category);
      meta.appendChild(el("span", "source-name", article.source || ""));
      meta.appendChild(el("time", "", formatDate(article.published_at)));
      root.appendChild(meta);

      root.appendChild(el("h1", "detail-title", article.title || ""));

      const image = document.createElement("img");
      image.className = "detail-image";
      image.src = article.thumbnail_url || defaultImages[article.category] || "";
      image.onerror = () => {
        image.onerror = null;
        image.src = defaultImages[article.category] || "";
      };
      image.alt = "";
      root.appendChild(image);

      const bodyBlock = el("section", "detail-block");
      bodyBlock.appendChild(el("h2", "", "本文（抜粋）"));
      const rawBodyText = article.article_body || article.summary || "";
      const bodyText = (rawBodyText.match(/�/g) || []).length >= 3
        ? "本文の文字コードを確認中です。内容は元記事でご覧いただけます。"
        : rawBodyText;
      const paragraphs = bodyText.split(/\\n+/).map((line) => line.trim()).filter(Boolean);
      if (paragraphs.length) {
        paragraphs.forEach((para) => bodyBlock.appendChild(el("p", "body-paragraph", para)));
      } else {
        bodyBlock.appendChild(el("p", "body-paragraph", bodyText));
      }
      bodyBlock.appendChild(createLink(article.url, "元記事で全文を読む", "source-link"));
      root.appendChild(bodyBlock);

      const points = (article.key_points || []).filter((point) => point && point.trim());
      if (points.length) {
        const pointsBlock = el("section", "detail-block");
        pointsBlock.appendChild(el("h2", "", "重要ポイント"));
        const list = document.createElement("ul");
        list.className = "point-list";
        points.slice(0, 3).forEach((point) => {
          list.appendChild(el("li", "", point));
        });
        pointsBlock.appendChild(list);
        root.appendChild(pointsBlock);
      }
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
        "AI最新情報（国内）": "ai-japan",
        "AI最新情報（国外）": "ai-global",
        "Apple（最新公式）": "apple-official",
        "Apple（リーク情報）": "apple-rumors",
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
