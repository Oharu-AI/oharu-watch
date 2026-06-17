"""Fetch RSS news, collect thumbnails, and save summarized articles."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from summarizer import SummarizerError, summarize_article


ARTICLES_PATH = Path("articles.json")
RETENTION_DAYS = 7
MAX_NEW_ARTICLES = int(os.environ.get("MAX_NEW_ARTICLES", "24"))
MAX_NEW_PER_CATEGORY = int(os.environ.get("MAX_NEW_PER_CATEGORY", "18"))
MAX_RESUMMARIZE_ARTICLES = int(os.environ.get("MAX_RESUMMARIZE_ARTICLES", "4"))
MAX_TRANSLATE_EXISTING_ARTICLES = int(os.environ.get("MAX_TRANSLATE_EXISTING_ARTICLES", "20"))
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
gemini_disabled_for_run = False

GEMINI_SUMMARY_KEYWORDS = [
    "openai",
    "chatgpt",
    "gpt",
    "anthropic",
    "claude",
    "google ai",
]

DIRECT_SOURCE_NAMES = [
    "iPhone Mania",
    "gori.me",
    "AppBank",
    "AIsmiley AIニュース",
    "AINOW",
    "ITmedia AI+",
    "OpenAI News",
    "Google AI Blog",
    "Hugging Face Blog",
    "NVIDIA AI Blog",
    "VentureBeat AI",
    "The Decoder",
    "MIT Technology Review AI",
    "TechCrunch AI",
    "The Verge AI",
    "MarkTechPost",
    "Synced",
]

ACTIVE_CATEGORIES = {"AI", "Apple"}
EXCLUDED_KEYWORDS = ["deepmind"]

CATEGORY_DEFAULT_IMAGES = {
    "AI": "assets/default-ai.png",
    "Apple": "assets/default-apple.png",
}

CATEGORY_KEYWORDS = {
    "AI": [
        "openai",
        "chatgpt",
        "codex",
        "claude",
        "gemini",
        "anthropic",
        "perplexity",
        "aiエージェント",
        "人工知能",
        "生成ai",
    ],
    "Apple": [
        "apple",
        "iphone",
        "ipad",
        "mac",
        "apple watch",
        "vision",
        "ios",
        "macos",
        "apple intelligence",
        "app store",
        "アプリ",
        "aiアプリ",
    ],
}


def google_news_url(query: str, hl: str = "ja", gl: str = "JP", ceid: str = "JP:ja") -> str:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "hl": hl,
            "gl": gl,
            "ceid": ceid,
        }
    )
    return f"https://news.google.com/rss/search?{params}"


FEEDS = [
    {
        "category": "Apple",
        "source": "iPhone Mania",
        "url": "https://iphone-mania.jp/feed/",
    },
    {
        "category": "Apple",
        "source": "gori.me",
        "url": "https://gori.me/feed",
    },
    {
        "category": "Apple",
        "source": "AppBank",
        "url": "https://www.appbank.net/feed",
    },
    {
        "category": "AI",
        "source": "AIsmiley AIニュース",
        "url": "https://aismiley.co.jp/ai_news/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "AINOW",
        "url": "https://ainow.ai/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "ITmedia AI+",
        "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "Google News AI",
        "url": google_news_url(
            "OpenAI OR ChatGPT OR Codex OR Claude OR Gemini OR Anthropic OR Perplexity OR AIエージェント"
        ),
    },
    {
        "category": "AI",
        "source": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "NVIDIA AI Blog",
        "url": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "The Decoder",
        "url": "https://the-decoder.com/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "MarkTechPost",
        "url": "https://www.marktechpost.com/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "Synced",
        "url": "https://syncedreview.com/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI",
        "source": "Google News Global AI",
        "url": google_news_url(
            "OpenAI OR ChatGPT OR Anthropic OR Claude OR Google AI OR Gemini OR Microsoft AI OR Meta AI OR Mistral AI OR Perplexity AI",
            hl="en",
            gl="US",
            ceid="US:en",
        ),
    },
    {
        "category": "Apple",
        "source": "Apple Newsroom",
        "url": "https://www.apple.com/newsroom/rss-feed.rss",
        "filter_keywords": False,
    },
    {
        "category": "Apple",
        "source": "Google News Apple",
        "url": google_news_url(
            "iPhone OR iPad OR Mac OR Apple Watch OR Vision Pro OR iOS OR macOS OR Apple Intelligence"
        ),
    },
]


@dataclass
class FeedItem:
    title: str
    category: str
    source: str
    source_url: str
    published_at: str
    url: str
    description: str


class OgImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            if key in {"og:image", "og:image:url", "twitter:image"}:
                content = attrs_dict.get("content", "").strip()
                if content:
                    self.images.append(content)
        if tag.lower() == "link" and attrs_dict.get("rel", "").lower() == "image_src":
            href = attrs_dict.get("href", "").strip()
            if href:
                self.images.append(href)


def main() -> int:
    global gemini_disabled_for_run
    gemini_disabled_for_run = False

    parser = argparse.ArgumentParser(description="Fetch and summarize OHARU WATCH articles.")
    parser.add_argument(
        "--allow-placeholder-summary",
        action="store_true",
        help="Use local fallback summaries when GEMINI_API_KEY is unavailable.",
    )
    args = parser.parse_args()

    existing_articles = load_articles()
    existing_articles = prune_old_articles(existing_articles)
    existing_articles = refresh_local_translations(existing_articles)
    existing_articles = refresh_fallback_summaries(existing_articles)
    existing_urls = {normalize_url(article.get("url", "")) for article in existing_articles}

    feed_items, failed_feed_count = collect_feed_items()
    if not feed_items and failed_feed_count == len(FEEDS):
        print("All feeds failed. articles.json was not changed.", file=sys.stderr)
        return 1

    new_items = select_new_items(feed_items, existing_urls)

    if not new_items:
        save_articles(sort_articles(existing_articles))
        print("No new articles. Existing articles were pruned and saved.")
        return 0

    new_articles = []
    for index, item in enumerate(new_items, start=1):
        print(f"Summarizing {index}/{len(new_items)}: {item.title}")
        thumbnail_url = fetch_article_image(item) or CATEGORY_DEFAULT_IMAGES.get(item.category, "")
        draft_article = {
            "id": article_id(item.url),
            "title": item.title,
            "category": item.category,
            "source": item.source,
            "source_url": item.source_url,
            "published_at": item.published_at,
            "url": item.url,
            "thumbnail_url": thumbnail_url,
            "description": item.description,
        }

        try:
            if gemini_disabled_for_run or not should_summarize_with_gemini(draft_article):
                summary_data = fallback_summary(draft_article)
            elif args.allow_placeholder_summary and not os.environ.get("GEMINI_API_KEY"):
                summary_data = fallback_summary(draft_article)
            else:
                summary_data = summarize_article(draft_article)
        except SummarizerError as exc:
            print(f"Gemini summarization failed. Using RSS fallback summary: {exc}", file=sys.stderr)
            disable_gemini_if_quota_error(exc)
            summary_data = fallback_summary(draft_article)

        new_articles.append(
            {
                "id": draft_article["id"],
                "title": draft_article["title"],
                "category": draft_article["category"],
                "source": draft_article["source"],
                "source_url": draft_article["source_url"],
                "published_at": draft_article["published_at"],
                "url": draft_article["url"],
                "thumbnail_url": draft_article["thumbnail_url"],
                "summary": summary_data["summary"],
                "article_body": summary_data["article_body"],
                "key_points": summary_data["key_points"],
                "importance": summary_data["importance"],
                "summary_source": summary_data["source"],
                "impact_for_me": "",
            }
        )
        time.sleep(0.8)

    combined_articles = sort_articles(new_articles + existing_articles)
    save_articles(combined_articles)
    print(f"Saved {len(new_articles)} new articles and {len(combined_articles)} total articles.")
    return 0


def load_articles() -> list[dict[str, Any]]:
    if not ARTICLES_PATH.exists():
        return []
    try:
        data = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [
        article
        for article in data
        if article.get("category") in ACTIVE_CATEGORIES and not contains_excluded_keyword(article)
    ]


def save_articles(articles: list[dict[str, Any]]) -> None:
    temp_path = ARTICLES_PATH.with_name(".articles.json.tmp")
    temp_path.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(ARTICLES_PATH)


def prune_old_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    kept = []
    for article in articles:
        published = parse_datetime(article.get("published_at", ""))
        if published >= cutoff:
            kept.append(article)
    return kept


def refresh_fallback_summaries(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not os.environ.get("GEMINI_API_KEY"):
        return articles

    refreshed = []
    refreshed_count = 0
    for article in articles:
        if (
            not needs_gemini_summary(article)
            or gemini_disabled_for_run
            or not should_summarize_with_gemini(article)
            or refreshed_count >= MAX_RESUMMARIZE_ARTICLES
        ):
            refreshed.append(article)
            continue

        try:
            summary_data = summarize_article(article)
        except SummarizerError as exc:
            print(f"Gemini re-summarization failed. Keeping fallback summary: {exc}", file=sys.stderr)
            disable_gemini_if_quota_error(exc)
            refreshed.append(article)
            continue

        updated_article = dict(article)
        updated_article["summary"] = summary_data["summary"]
        updated_article["article_body"] = summary_data["article_body"]
        updated_article["key_points"] = summary_data["key_points"]
        updated_article["importance"] = summary_data["importance"]
        updated_article["summary_source"] = summary_data["source"]
        refreshed.append(updated_article)
        refreshed_count += 1
        time.sleep(0.8)

    return refreshed


def refresh_local_translations(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refreshed = []
    translated_count = 0
    for article in articles:
        if (
            translated_count >= MAX_TRANSLATE_EXISTING_ARTICLES
            or article.get("summary_source") == "gemini"
            or not is_likely_english(" ".join([str(article.get("summary", "")), str(article.get("article_body", ""))]))
        ):
            refreshed.append(article)
            continue

        title = clean_text(article.get("title", ""))
        text = clean_text(article.get("article_body") or article.get("summary") or article.get("description") or title)
        translated_title = translate_to_japanese(title) if is_likely_english(title) else ""
        translated = translate_to_japanese(text) if is_likely_english(text) else ""
        if translated_title and (not translated or translated == text):
            translated = text.replace(title, translated_title) if title in text else f"{translated_title}に関するニュースです。詳細は元記事で確認できます。"
        if not translated:
            refreshed.append(article)
            continue

        updated_article = dict(article)
        updated_article["summary"] = translated[:260]
        updated_article["article_body"] = translated
        updated_article["key_points"] = [
            "英語記事の概要を日本語に翻訳して表示しています。",
            "詳細は元記事リンクから確認できます。",
            "機械翻訳のため、固有名詞や専門用語は元記事も確認してください。",
        ]
        updated_article["summary_source"] = "translated_fallback"
        refreshed.append(updated_article)
        translated_count += 1
        time.sleep(0.2)
    return refreshed


def needs_gemini_summary(article: dict[str, Any]) -> bool:
    if article.get("summary_source") == "fallback":
        return True
    key_points = article.get("key_points", [])
    if any("Gemini要約はAPIキー" in str(point) for point in key_points):
        return True
    if any("要約生成に失敗" in str(point) for point in key_points):
        return True
    return "Gemini APIキー設定後" in str(article.get("summary", ""))


def should_summarize_with_gemini(article: dict[str, Any]) -> bool:
    if article.get("category") != "AI":
        return False

    haystack = " ".join(
        str(article.get(key, ""))
        for key in ["title", "description", "summary", "source", "source_url", "url"]
    ).lower()
    return any(keyword in haystack for keyword in GEMINI_SUMMARY_KEYWORDS)


def disable_gemini_if_quota_error(exc: SummarizerError) -> None:
    global gemini_disabled_for_run
    if "HTTP 429" in str(exc):
        gemini_disabled_for_run = True
        print("Gemini quota/rate limit reached. Skipping Gemini summaries for the rest of this run.", file=sys.stderr)


def collect_feed_items() -> tuple[list[FeedItem], int]:
    items: list[FeedItem] = []
    failed_feed_count = 0
    for feed in FEEDS:
        try:
            xml_text = fetch_text(feed["url"])
            parsed_items = parse_feed(xml_text, feed)
            items.extend(parsed_items)
            print(f"Fetched {len(parsed_items)} items from {feed['source']}")
        except Exception as exc:
            failed_feed_count += 1
            print(f"Skipped feed {feed['source']}: {exc}", file=sys.stderr)
    return items, failed_feed_count


def fetch_text(url: str, timeout: int = 20, max_bytes: int = 2_000_000) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, text/html;q=0.7, */*;q=0.6",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        charset_match = re.search(r"charset=([\w-]+)", content_type, re.I)
        charset = charset_match.group(1) if charset_match else "utf-8"
        data = response.read(max_bytes)
    return data.decode(charset, errors="replace")


def parse_feed(xml_text: str, feed: dict[str, Any]) -> list[FeedItem]:
    root = ET.fromstring(xml_text)
    category = feed["category"]
    default_source = feed["source"]
    should_filter = feed.get("filter_keywords", True)
    entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

    items = []
    for entry in entries[:30]:
        title = clean_text(find_text(entry, ["title", "{http://www.w3.org/2005/Atom}title"]))
        url = find_link(entry)
        description = clean_text(
            find_text(
                entry,
                [
                    "description",
                    "summary",
                    "{http://www.w3.org/2005/Atom}summary",
                    "{http://purl.org/rss/1.0/modules/content/}encoded",
                ],
            )
        )
        source = clean_text(find_text(entry, ["source", "{http://www.w3.org/2005/Atom}source"])) or default_source
        source_url = find_source_url(entry)
        published_raw = find_text(
            entry,
            [
                "pubDate",
                "published",
                "updated",
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated",
                "{http://purl.org/dc/elements/1.1/}date",
            ],
        )
        published_at = parse_datetime(published_raw).isoformat()

        if not title or not url:
            continue
        if contains_excluded_keyword({"title": title, "description": description, "source": source, "url": url}):
            continue
        if should_filter and not matches_category(title, description, category):
            continue

        items.append(
            FeedItem(
                title=title,
                category=category,
                source=source,
                source_url=source_url,
                published_at=published_at,
                url=url,
                description=description,
            )
        )
    return items


def find_text(entry: ET.Element, names: list[str]) -> str:
    for name in names:
        found = entry.find(name)
        if found is not None:
            return "".join(found.itertext()).strip()
    return ""


def find_link(entry: ET.Element) -> str:
    link = find_text(entry, ["link", "{http://www.w3.org/2005/Atom}link"])
    if link:
        return link.strip()
    for link_element in entry.findall("{http://www.w3.org/2005/Atom}link"):
        href = link_element.attrib.get("href", "").strip()
        if href:
            return href
    return ""


def find_source_url(entry: ET.Element) -> str:
    for name in ["source", "{http://www.w3.org/2005/Atom}source"]:
        found = entry.find(name)
        if found is not None:
            return found.attrib.get("url", "").strip()
    return ""


def matches_category(title: str, description: str, category: str) -> bool:
    haystack = f"{title} {description}".lower()
    return any(keyword.lower() in haystack for keyword in CATEGORY_KEYWORDS.get(category, []))


def contains_excluded_keyword(article: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(article.get(key, ""))
        for key in ["title", "description", "summary", "article_body", "source", "url"]
    ).lower()
    return any(keyword in haystack for keyword in EXCLUDED_KEYWORDS)


def select_new_items(items: list[FeedItem], existing_urls: set[str]) -> list[FeedItem]:
    seen: set[str] = set()
    selected: list[FeedItem] = []
    per_category: dict[str, int] = {}
    fresh_items = [item for item in items if parse_datetime(item.published_at) >= datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)]
    fresh_items.sort(key=lambda item: parse_datetime(item.published_at), reverse=True)

    def consider(item: FeedItem) -> bool:
        normalized = normalize_url(item.url)
        if not normalized or normalized in existing_urls or normalized in seen:
            return False
        category_count = per_category.get(item.category, 0)
        if category_count >= MAX_NEW_PER_CATEGORY:
            return False
        selected.append(item)
        seen.add(normalized)
        per_category[item.category] = category_count + 1
        return len(selected) >= MAX_NEW_ARTICLES

    for source in DIRECT_SOURCE_NAMES:
        source_items = [item for item in fresh_items if item.source == source]
        if source_items and consider(source_items[0]):
            return selected

    direct_items = [item for item in fresh_items if item.source in DIRECT_SOURCE_NAMES]
    other_items = [item for item in fresh_items if item.source not in DIRECT_SOURCE_NAMES]
    for item in direct_items + other_items:
        if consider(item):
            break
    return selected


def fetch_article_image(item: FeedItem) -> str:
    for url in [item.url, item.source_url]:
        image_url = fetch_og_image(url)
        if image_url and not is_unhelpful_thumbnail(image_url):
            return image_url
    return ""


def fetch_og_image(url: str) -> str:
    if not url:
        return ""
    try:
        html_text = fetch_text(url, timeout=12, max_bytes=1_200_000)
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError):
        return ""

    parser = OgImageParser()
    try:
        parser.feed(html_text)
    except Exception:
        return ""

    for image_url in parser.images:
        absolute_url = urllib.parse.urljoin(url, html.unescape(image_url))
        if absolute_url.startswith(("http://", "https://")):
            return absolute_url
    return ""


def is_unhelpful_thumbnail(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return parsed.netloc == "lh3.googleusercontent.com" and parsed.path.startswith("/J6_coFbogxhRI9iM864NL")


def fallback_summary(article: dict[str, Any]) -> dict[str, Any]:
    title = article.get("title", "この記事")
    description = clean_text(article.get("description", ""))
    source = "fallback"
    translated_title = translate_to_japanese(title) if is_likely_english(str(title)) else ""
    if is_likely_english(description or title):
        translated = translate_to_japanese(description or title)
        if translated:
            description = translated
            source = "translated_fallback"
    if not description and translated_title:
        description = f"{translated_title}に関するニュースです。詳細は元記事で確認できます。"
        source = "translated_fallback"
    summary = description[:260] if description else f"この記事は「{title}」についてのニュースです。詳細は元記事で確認できます。"
    return {
        "summary": summary,
        "article_body": summary,
        "key_points": [
            "RSSから記事情報を取得しています。",
            "要約生成に失敗した場合はRSS概要を表示します。",
            "元記事で詳細を確認できます。",
        ],
        "importance": 3,
        "source": source,
    }


def is_likely_english(text: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return False
    ascii_letters = sum(ch.isascii() and ch.isalpha() for ch in cleaned)
    japanese_chars = sum("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in cleaned)
    return ascii_letters >= 40 and ascii_letters > japanese_chars * 2


def translate_to_japanese(text: str) -> str:
    source_text = clean_text(text)[:1200]
    if not source_text:
        return ""
    params = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "auto",
            "tl": "ja",
            "dt": "t",
            "q": source_text,
        }
    )
    request = urllib.request.Request(
        f"https://translate.googleapis.com/translate_a/single?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return ""
    try:
        return clean_text("".join(part[0] for part in data[0] if part and part[0]))
    except (IndexError, TypeError):
        return ""


def parse_datetime(value: str) -> datetime:
    if isinstance(value, datetime):
        date = value
    else:
        text = str(value or "").strip()
        if not text:
            return datetime.now(timezone.utc)
        try:
            date = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            normalized = text.replace("Z", "+00:00")
            try:
                date = datetime.fromisoformat(normalized)
            except ValueError:
                return datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc)


def sort_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(articles, key=lambda article: parse_datetime(article.get("published_at", "")), reverse=True)


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(str(url or "").strip())
    query_pairs = [
        (key, value)
        for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}
    ]
    return urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            urllib.parse.urlencode(query_pairs),
            "",
        )
    )


def article_id(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:16]


def clean_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


if __name__ == "__main__":
    raise SystemExit(main())
