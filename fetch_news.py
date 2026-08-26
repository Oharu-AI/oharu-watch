"""Fetch RSS news, collect thumbnails, and save summarized articles."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import socket
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
# Gemini要約は既定で停止（USE_GEMINI_SUMMARY=1 で復活）。
# 停止時は全記事「本文の抜粋＋元記事リンク」方式。英語記事のみ無料翻訳を使う。
USE_GEMINI_SUMMARY = os.environ.get("USE_GEMINI_SUMMARY", "0") == "1"
MAX_NEW_ARTICLES = int(os.environ.get("MAX_NEW_ARTICLES", "48"))
# カテゴリ別の1日あたり新規上限。国内AIを最優先に、次いで海外AI、
# Apple公式、Appleのリーク・周辺情報を集める。
CATEGORY_NEW_LIMITS = {
    "AI最新情報（国内）": int(os.environ.get("MAX_NEW_AI_JAPAN", "28")),
    "AI最新情報（国外）": int(os.environ.get("MAX_NEW_AI_GLOBAL", "16")),
    "Apple（最新公式）": int(os.environ.get("MAX_NEW_APPLE_OFFICIAL", "6")),
    "Apple（リーク情報）": int(os.environ.get("MAX_NEW_APPLE_RUMORS", "12")),
}
MAX_NEW_PER_CATEGORY = int(os.environ.get("MAX_NEW_PER_CATEGORY", str(MAX_NEW_ARTICLES)))
MAX_RESUMMARIZE_ARTICLES = int(os.environ.get("MAX_RESUMMARIZE_ARTICLES", "4"))
MAX_TRANSLATE_EXISTING_ARTICLES = int(os.environ.get("MAX_TRANSLATE_EXISTING_ARTICLES", "120"))
# 本文抜粋の文字数。カード用（短め）と詳細ページ用（たっぷり）。
EXCERPT_SUMMARY_CHARS = int(os.environ.get("EXCERPT_SUMMARY_CHARS", "180"))
EXCERPT_BODY_CHARS = int(os.environ.get("EXCERPT_BODY_CHARS", "6000"))
TRANSLATION_REQUEST_INTERVAL = float(os.environ.get("TRANSLATION_REQUEST_INTERVAL", "0.8"))
FETCH_ARTICLE_PAGES = os.environ.get("FETCH_ARTICLE_PAGES", "0") == "1"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
gemini_disabled_for_run = False
translation_disabled_for_run = False
last_translation_request_at = 0.0

GEMINI_SUMMARY_KEYWORDS = [
    "openai",
    "chatgpt",
    "gpt",
    "anthropic",
    "claude",
    "google ai",
]

CATEGORIES = [
    "AI最新情報（国内）",
    "AI最新情報（国外）",
    "Apple（最新公式）",
    "Apple（リーク情報）",
]

DIRECT_SOURCE_NAMES = [
    "AIsmiley AIニュース",
    "AINOW",
    "ITmedia AI+",
    "Publickey",
    "Impress Watch",
    "Sakana AI",
    "CyberAgent AI Lab",
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
    "Apple Newsroom",
    "iPhone Mania",
    "gori.me",
    "AppBank",
    "Mac Otakara",
    "AAPL Ch.",
    "MacRumors",
]

ACTIVE_CATEGORIES = set(CATEGORIES)
EXCLUDED_KEYWORDS = ["deepmind"]

# 無料翻訳が残しやすい技術用語を、ニュースに詳しくない読者にも意味が伝わる表現へ整える。
# 製品名や数値は変えず、意味を一意に説明できる語だけを対象にする。
READER_FRIENDLY_TITLE_REPLACEMENTS = [
    (r"クロード", "Claude"),
    (r"AI[・ ]?モデル", "AIモデル"),
    (r"コーディング[・ ]?エージェント", "プログラミング支援AI"),
    (r"AI[・ ]?エージェント", "自律型AI"),
    (r"サブ[・ ]?エージェント", "補助AI"),
    (r"インタラクティブ推論ベンチマーク", "対話型の推論能力テスト"),
    (r"エージェント[・ ]?ベンチマーク", "AIエージェントの性能テスト"),
    (r"ベンチマーク", "性能テスト"),
    (r"プロンプト[・ ]?インジェクション", "悪意ある指示を読み込ませる攻撃"),
    (r"プロンプトを挿入し", "悪意ある指示を紛れ込ませ"),
    (r"プロンプトを挿入", "悪意ある指示を紛れ込ませる"),
    (r"ファイン[・ ]?チューニング", "追加学習"),
    (r"マルチ[・ ]?モーダル", "文章・画像・音声を扱えるAI"),
    (r"ハーネス", "AIを実際に動かす仕組み"),
    (r"ベンチャー[・ ]?キャピタル", "スタートアップ投資会社"),
    (r"オープン[・ ]?ウェイト", "モデルデータを公開した"),
    (r"量子化対応蒸留", "軽量化しやすい小型AIを作る技術"),
    (r"エンド[・ ]?ツー[・ ]?エンド", "一連の"),
    (r"ドキュメントインテリジェンスパイプライン", "文書を読み取って整理する処理"),
    (r"パイプライン", "一連の処理"),
    (r"検索[・ ]?API", "検索API"),
    (r"検出[・ ]?API", "検出API"),
    (r"AI[・ ]?テキスト", "AI生成文"),
    (r"Flash[・ ]?ビジョンモデル", "Flash視覚AIモデル"),
]

# Reddit の人気スレッドを拾う対象サブレディット。
# 1本のフィードURLにまとめるので、増やしてもリクエストは1回のまま。
REDDIT_AI_SUBREDDITS = [
    "OpenAI",
    "ClaudeAI",
    "LocalLLaMA",
    "singularity",
    "Anthropic",
]

# 各サブレディットに1枠ずつ確保する（優先枠に入れないと通常ニュースに埋もれて0件になる）。
DIRECT_SOURCE_NAMES += [f"Reddit r/{sub}" for sub in REDDIT_AI_SUBREDDITS]

# 本文を持たないリンク投稿のときに表示する文言。
REDDIT_LINK_POST_BODY = "Redditで話題になっているスレッドです。リンク先の記事と議論は元スレッドで確認できます。"

# サブレディット1つあたり何スレッド採用するか。
# top/.rss?t=day は人気順に並ぶので、先頭から取る＝その日の人気スレッドになる。
# （RedditのJSON APIは403で使えず、RSSにはスコアが無いためこの並び順が唯一の人気指標）
REDDIT_TOP_PER_SUB = int(os.environ.get("REDDIT_TOP_PER_SUB", "1"))
# Redditの人気スレッドも通常更新に含める。障害時だけ ENABLE_REDDIT=0 で停止できる。
ENABLE_REDDIT = os.environ.get("ENABLE_REDDIT", "1") == "1"

CATEGORY_DEFAULT_IMAGES = {
    "AI最新情報（国内）": "assets/default-ai.png",
    "AI最新情報（国外）": "assets/default-ai.png",
    "Apple（最新公式）": "assets/default-apple.png",
    "Apple（リーク情報）": "assets/default-apple.png",
}

CATEGORY_KEYWORDS = {
    "AI最新情報（国内）": [
        "openai",
        "chatgpt",
        "codex",
        "claude",
        "gemini",
        "anthropic",
        "perplexity",
        "sakana ai",
        "preferred networks",
        "pfn",
        "plamo",
        "pksha",
        "abeja",
        "rinna",
        "cyberagent ai",
        "サカナai",
        "プリファードネットワークス",
        "サイバーエージェントai",
        "copilot",
        "microsoft ai",
        "aiエージェント",
        "ai活用",
        "ai導入",
        "aiモデル",
        "チャットgpt",
        "大規模言語モデル",
        "llm",
        "人工知能",
        "生成ai",
    ],
    "Apple（リーク情報）": [
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
        "category": "Apple（リーク情報）",
        "source": "iPhone Mania",
        "url": "https://iphone-mania.jp/feed/",
    },
    {
        "category": "Apple（リーク情報）",
        "source": "gori.me",
        "url": "https://gori.me/feed",
    },
    {
        "category": "Apple（リーク情報）",
        "source": "AppBank",
        "url": "https://www.appbank.net/feed",
    },
    {
        "category": "AI最新情報（国内）",
        "source": "AIsmiley AIニュース",
        "url": "https://aismiley.co.jp/ai_news/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国内）",
        "source": "AINOW",
        "url": "https://ainow.ai/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国内）",
        "source": "ITmedia AI+",
        "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Publickey",
        "url": "https://www.publickey1.jp/atom.xml",
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Impress Watch",
        "url": "https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf",
    },
    {
        "category": "AI最新情報（国外）",
        "source": "Microsoft AI",
        "url": "https://blogs.microsoft.com/feed/",
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Ledge.ai",
        "url": google_news_url("site:ledge.ai"),
        "filter_keywords": False,
    },
    {
        # 複数サブレディットを "+" でまとめ、1リクエストで人気スレッドを取得する。
        # Redditはレート制限が厳しく、サブレディットごとに叩くと429で落ちるため。
        # top/.rss?t=day = 直近24時間で人気（スコア上位）のスレッド。
        "category": "AI最新情報（国外）",
        "source": "Reddit AI",
        "url": (
            "https://www.reddit.com/r/"
            + "+".join(REDDIT_AI_SUBREDDITS)
            + "/top/.rss?t=day"
        ),
        "filter_keywords": False,
        "reddit": True,
        "enabled": ENABLE_REDDIT,
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Sakana AI",
        "url": "https://sakana.ai/feed.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国内）",
        "source": "CyberAgent AI Lab",
        "url": "https://research.cyberagent.ai/news/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Google News 国内AI企業",
        "url": google_news_url(
            "Sakana AI OR サカナAI OR Preferred Networks OR PFN OR PLaMo OR PKSHA OR ABEJA OR rinna OR CyberAgent AI Lab OR NEC 生成AI OR NTT DATA 生成AI"
        ),
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Google News 国内AI",
        "url": google_news_url(
            "OpenAI OR ChatGPT OR Codex OR Claude OR Gemini OR Anthropic OR Perplexity OR AIエージェント"
        ),
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Google News Anthropic",
        "url": google_news_url(
            "Anthropic OR Claude OR \"Claude AI\" OR \"Claude Code\""
        ),
    },
    {
        "category": "AI最新情報（国内）",
        "source": "Google News 国内AIメディア",
        "url": google_news_url(
            "(生成AI OR 人工知能 OR AIエージェント) (site:ledge.ai OR site:aismiley.co.jp OR site:ainow.ai OR site:itmedia.co.jp OR site:watch.impress.co.jp OR site:ascii.jp OR site:publickey1.jp)"
        ),
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "Google News 海外AI大手",
        "url": google_news_url(
            "Meta AI OR Llama OR Mistral AI OR Microsoft Copilot OR xAI Grok",
            hl="en",
            gl="US",
            ceid="US:en",
        ),
    },
    {
        "category": "AI最新情報（国外）",
        "source": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "NVIDIA AI Blog",
        "url": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "The Decoder",
        "url": "https://the-decoder.com/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "MarkTechPost",
        "url": "https://www.marktechpost.com/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "Synced",
        "url": "https://syncedreview.com/feed/",
        "filter_keywords": False,
    },
    {
        "category": "AI最新情報（国外）",
        "source": "Google News Global AI",
        "url": google_news_url(
            "OpenAI OR ChatGPT OR Anthropic OR Claude OR Google AI OR Gemini OR Microsoft AI OR Meta AI OR Mistral AI OR Perplexity AI",
            hl="en",
            gl="US",
            ceid="US:en",
        ),
    },
    {
        "category": "Apple（リーク情報）",
        "source": "MacRumors",
        "url": "https://feeds.macrumors.com/MacRumors-All",
        "filter_keywords": False,
    },
    {
        "category": "Apple（リーク情報）",
        "source": "Mac Otakara",
        "url": "https://www.macotakara.jp/rss2.xml",
        "filter_keywords": False,
    },
    {
        "category": "Apple（リーク情報）",
        "source": "AAPL Ch.",
        "url": "https://applech2.com/feed",
        "filter_keywords": False,
    },
    {
        "category": "Apple（最新公式）",
        "source": "Apple Newsroom",
        "url": "https://www.apple.com/newsroom/rss-feed.rss",
        "filter_keywords": False,
    },
    {
        "category": "Apple（最新公式）",
        "source": "Apple Developer News",
        "url": "https://developer.apple.com/news/releases/rss/releases.rss",
        "filter_keywords": False,
    },
    {
        "category": "Apple（リーク情報）",
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


class ArticleTextParser(HTMLParser):
    """元記事HTMLの <p> 段落から読める本文だけを抽出する簡易リーダー。"""

    SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "figure"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0
        self._in_p = 0
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip += 1
        elif tag == "p" and self._skip == 0:
            self._in_p += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip > 0:
            self._skip -= 1
        elif tag == "p" and self._in_p > 0:
            self._in_p -= 1
            text = clean_text("".join(self._buffer))
            if len(text) >= 20:
                self.parts.append(text)
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._skip == 0 and self._in_p > 0:
            self._buffer.append(data)


def main() -> int:
    global gemini_disabled_for_run, translation_disabled_for_run, last_translation_request_at
    gemini_disabled_for_run = False
    translation_disabled_for_run = False
    last_translation_request_at = 0.0

    parser = argparse.ArgumentParser(description="Fetch and summarize OHARU WATCH articles.")
    parser.add_argument(
        "--allow-placeholder-summary",
        action="store_true",
        help="Use local fallback summaries when GEMINI_API_KEY is unavailable.",
    )
    args = parser.parse_args()
    _page_cache.clear()

    existing_articles = load_articles()
    existing_articles = prune_old_articles(existing_articles)
    existing_articles = deduplicate_articles(existing_articles)
    existing_articles = refresh_local_translations(existing_articles)
    existing_articles = refresh_reader_friendly_titles(existing_articles)
    existing_articles = refresh_fallback_summaries(existing_articles)
    existing_urls = {normalize_url(article.get("url", "")) for article in existing_articles}
    existing_title_keys = {article_title_key(article.get("title", "")) for article in existing_articles}

    feed_items, failed_feed_count = collect_feed_items()
    enabled_feed_count = sum(feed.get("enabled", True) for feed in FEEDS)
    if not feed_items and failed_feed_count == enabled_feed_count:
        print("All feeds failed. articles.json was not changed.", file=sys.stderr)
        return 1

    existing_articles = refresh_global_summaries_from_feeds(existing_articles, feed_items)

    new_items = select_new_items(feed_items, existing_urls, existing_title_keys)

    if not new_items:
        save_articles(sort_articles(existing_articles))
        print("No new articles. Existing articles were pruned and saved.")
        return 0

    new_articles = []
    for index, item in enumerate(new_items, start=1):
        print(f"Summarizing {index}/{len(new_items)}: {item.title}")
        if is_reddit_url(item.url):
            # Redditはページを取りに行くと429で締め出されるため、フィード取得1回で完結させる。
            # サムネイルはカテゴリ既定画像、本文はRSSの内容をそのまま使う。
            thumbnail_url = CATEGORY_DEFAULT_IMAGES.get(item.category, "")
            # リンク投稿は本文が無いので、スレッドへ誘導する文言にする。
            description = item.description or REDDIT_LINK_POST_BODY
        elif FETCH_ARTICLE_PAGES:
            thumbnail_url = fetch_article_image(item) or CATEGORY_DEFAULT_IMAGES.get(item.category, "")
            # 元記事ページ本文を抽出し、RSS概要より充実していれば本文として使う。
            article_text = fetch_article_body(item.url)
            description = article_text if len(article_text) > len(item.description) else item.description
        else:
            thumbnail_url = CATEGORY_DEFAULT_IMAGES.get(item.category, "")
            description = item.description
        _page_cache.pop(item.url, None)
        _page_cache.pop(item.source_url, None)
        draft_article = {
            "id": article_id(item.url),
            "title": item.title,
            "category": item.category,
            "source": item.source,
            "source_url": item.source_url,
            "published_at": item.published_at,
            "url": item.url,
            "thumbnail_url": thumbnail_url,
            "description": description,
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
                "title": make_title_reader_friendly(
                    summary_data.get("title") or draft_article["title"],
                    draft_article["title"],
                    draft_article["source"],
                ),
                "original_title": draft_article["title"]
                if summary_data.get("title") and summary_data.get("title") != draft_article["title"]
                else "",
                "category": draft_article["category"],
                "source": draft_article["source"],
                "source_url": draft_article["source_url"],
                "published_at": draft_article["published_at"],
                "url": draft_article["url"],
                "thumbnail_url": draft_article["thumbnail_url"],
                "summary": summary_data["summary"],
                "article_body": summary_data["article_body"],
                "description": draft_article["description"],
                "key_points": summary_data["key_points"],
                "importance": summary_data["importance"],
                "summary_source": summary_data["source"],
                "impact_for_me": "",
            }
        )
        if USE_GEMINI_SUMMARY:
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
    articles = []
    for article in data:
        normalized_article = dict(article)
        normalized_article["category"] = normalize_category(normalized_article)
        if normalized_article["category"] in ACTIVE_CATEGORIES and not contains_excluded_keyword(normalized_article):
            articles.append(normalized_article)
    return articles


def normalize_category(article: dict[str, Any]) -> str:
    """旧2カテゴリの記事も、現在の4カテゴリへ安全に振り分ける。"""
    category = str(article.get("category", ""))
    if category in ACTIVE_CATEGORIES:
        return category
    if category == "Apple":
        source = str(article.get("source", ""))
        url = str(article.get("url", ""))
        if source.startswith("Apple ") or "apple.com/" in url:
            return "Apple（最新公式）"
        return "Apple（リーク情報）"
    if category == "AI":
        source = str(article.get("source", ""))
        source_url = str(article.get("source_url", ""))
        url = str(article.get("url", ""))
        domestic_sources = {
            "AIsmiley AIニュース",
            "AINOW",
            "ITmedia AI+",
            "Ledge.ai",
            "Sakana AI",
            "CyberAgent AI Lab",
            "窓の杜",
            "クラウド Watch",
            "デジタルクロス",
            "ビジネス+IT",
        }
        if source in domestic_sources or any(".jp" in value for value in [source_url, url]):
            return "AI最新情報（国内）"
        return "AI最新情報（国外）"
    return category


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
        english_text = " ".join(
            [
                str(article.get("summary", "")),
                str(article.get("article_body", "")),
            ]
        )
        title = clean_text(article.get("title", ""))
        text = clean_text(article.get("article_body") or article.get("summary") or article.get("description") or title)
        is_global_article = article.get("category") == "AI最新情報（国外）"
        has_english_title = is_likely_english_title(title)
        has_english_body = is_likely_english(english_text) or (
            is_global_article
            and (needs_japanese_translation(text) or (has_english_title and title in text))
        )
        if translated_count >= MAX_TRANSLATE_EXISTING_ARTICLES or (
            article.get("summary_source") == "gemini" and not has_english_title and not has_english_body
        ) or not (has_english_title or has_english_body):
            refreshed.append(article)
            continue

        translated_title = translate_to_japanese(title) if is_likely_english_title(title) else ""
        if has_english_body and is_placeholder_summary(text) and translated_title:
            translated = f"「{translated_title}」に関する国外ニュースです。続きは元記事で確認できます。"
        else:
            translated = translate_to_japanese(text) if has_english_body else ""
        if not translated and not translated_title:
            refreshed.append(article)
            continue

        updated_article = dict(article)
        if translated_title:
            updated_article.setdefault("original_title", title)
            updated_article["title"] = translated_title
        if translated:
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


def refresh_reader_friendly_titles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """保存済みの翻訳タイトルにも、読み手向けの用語整理を反映する。"""
    refreshed = []
    for article in articles:
        updated_article = dict(article)
        updated_article["title"] = make_title_reader_friendly(
            str(article.get("title", "")),
            str(article.get("original_title", "")),
            str(article.get("source", "")),
        )
        refreshed.append(updated_article)
    return refreshed


def refresh_global_summaries_from_feeds(
    articles: list[dict[str, Any]], feed_items: list[FeedItem]
) -> list[dict[str, Any]]:
    """翻訳失敗時の定型文を、再取得できたRSSの説明文から日本語要約へ戻す。"""
    descriptions = {
        normalize_url(item.url): item.description
        for item in feed_items
        if item.category == "AI最新情報（国外）" and clean_text(item.description)
    }
    refreshed = []
    for article in articles:
        summary = str(article.get("summary", ""))
        raw = descriptions.get(normalize_url(article.get("url", "")), "")
        if (
            article.get("category") != "AI最新情報（国外）"
            or not raw
            or not is_placeholder_summary(summary)
        ):
            refreshed.append(article)
            continue

        paragraphs = split_paragraphs(raw)
        body = build_body(paragraphs, EXCERPT_BODY_CHARS, translate=needs_japanese_translation(raw))
        if not body:
            refreshed.append(article)
            continue

        updated_article = dict(article)
        updated_article["description"] = raw
        updated_article["summary"] = trim_excerpt(body, EXCERPT_SUMMARY_CHARS)
        updated_article["article_body"] = body
        updated_article["summary_source"] = (
            "translated_fallback" if needs_japanese_translation(raw) else "fallback"
        )
        refreshed.append(updated_article)
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
    if not USE_GEMINI_SUMMARY:
        return False
    if not str(article.get("category", "")).startswith("AI"):
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
        if not feed.get("enabled", True):
            print(f"Skipped feed {feed['source']}: disabled")
            continue
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


REDDIT_HOSTS = {"www.reddit.com", "reddit.com", "old.reddit.com"}
# RedditのRSS本文末尾に必ず付く定型文（"submitted by /u/... to r/... [link] [comments]"）。
# 中身のあるリンク投稿と区別できないので落とす。
REDDIT_BOILERPLATE_RE = re.compile(r"submitted by\s*/u/.*$", re.I | re.S)


def is_reddit_url(url: str) -> bool:
    return urllib.parse.urlsplit(url).netloc.lower() in REDDIT_HOSTS


def subreddit_of(entry: ET.Element, url: str) -> str:
    """エントリが属するサブレディット名（例: ClaudeAI）を返す。"""
    category_element = entry.find("{http://www.w3.org/2005/Atom}category")
    if category_element is not None:
        label = category_element.attrib.get("label", "")
        if label.startswith("r/"):
            return label[2:]
    match = re.search(r"/r/([^/]+)/", url)
    return match.group(1) if match else ""


def clean_reddit_body(text: str) -> str:
    """Reddit本文から定型文を除く。実質空ならスレッドへ誘導する文言にする。"""
    body = REDDIT_BOILERPLATE_RE.sub("", text).strip()
    return body


def parse_reddit_feed(xml_text: str, feed: dict[str, Any]) -> list[FeedItem]:
    """Redditの人気スレッドを、サブレディットごとに上位から取り出す。

    top/.rss?t=day はスコア順に並ぶため、フィードの並び順を保ったまま
    サブレディットごとに先頭 REDDIT_TOP_PER_SUB 件だけ採用する。
    日付順に並べ替えると人気順が壊れるので、ここで絞り切るのが要点。
    """
    atom = "{http://www.w3.org/2005/Atom}"
    root = ET.fromstring(xml_text)
    per_sub: dict[str, int] = {}
    items: list[FeedItem] = []

    for entry in root.findall(f".//{atom}entry"):
        title = clean_text(find_text(entry, [f"{atom}title"]))
        url = find_link(entry)
        if not title or not url:
            continue

        sub = subreddit_of(entry, url)
        if not sub:
            continue
        if per_sub.get(sub, 0) >= REDDIT_TOP_PER_SUB:
            continue

        content_element = entry.find(f"{atom}content")
        raw_body = "".join(content_element.itertext()) if content_element is not None else ""
        body = clean_reddit_body(clean_text(raw_body))

        candidate = {"title": title, "description": body, "source": f"r/{sub}", "url": url}
        if contains_excluded_keyword(candidate):
            continue

        per_sub[sub] = per_sub.get(sub, 0) + 1
        items.append(
            FeedItem(
                title=title,
                category=feed["category"],
                source=f"Reddit r/{sub}",
                source_url=f"https://www.reddit.com/r/{sub}/",
                published_at=parse_datetime(find_text(entry, [f"{atom}updated", f"{atom}published"])).isoformat(),
                url=url,
                description=body,
            )
        )
    return items


def parse_feed(xml_text: str, feed: dict[str, Any]) -> list[FeedItem]:
    if feed.get("reddit"):
        return parse_reddit_feed(xml_text, feed)

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
    keywords = CATEGORY_KEYWORDS.get(category)
    if keywords is None and category.startswith("AI"):
        keywords = CATEGORY_KEYWORDS["AI最新情報（国内）"]
    return any(keyword.lower() in haystack for keyword in (keywords or []))


def contains_excluded_keyword(article: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(article.get(key, ""))
        for key in ["title", "description", "summary", "article_body", "source", "url"]
    ).lower()
    return any(keyword in haystack for keyword in EXCLUDED_KEYWORDS)


def select_new_items(
    items: list[FeedItem], existing_urls: set[str], existing_title_keys: set[str]
) -> list[FeedItem]:
    seen: set[str] = set()
    seen_titles = set(existing_title_keys)
    selected: list[FeedItem] = []
    per_category: dict[str, int] = {}
    fresh_items = [item for item in items if parse_datetime(item.published_at) >= datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)]
    fresh_items.sort(key=lambda item: parse_datetime(item.published_at), reverse=True)

    def consider(item: FeedItem) -> bool:
        normalized = normalize_url(item.url)
        title_key = article_title_key(item.title)
        if not normalized or normalized in existing_urls or normalized in seen or (title_key and title_key in seen_titles):
            return False
        category_count = per_category.get(item.category, 0)
        category_limit = CATEGORY_NEW_LIMITS.get(item.category, MAX_NEW_PER_CATEGORY)
        if category_count >= category_limit:
            return False
        selected.append(item)
        seen.add(normalized)
        if title_key:
            seen_titles.add(title_key)
        per_category[item.category] = category_count + 1
        return len(selected) >= MAX_NEW_ARTICLES

    # 4カテゴリは毎回最低1本を確保した上で、国内AI → 海外AI → Apple公式 →
    # Appleリークの順で残りを追加する。
    ordered_items: list[FeedItem] = []
    category_items_by_name: dict[str, list[FeedItem]] = {}
    for category in CATEGORIES:
        category_items = [item for item in fresh_items if item.category == category]
        category_items_by_name[category] = category_items
        direct_items = [item for item in category_items if item.source in DIRECT_SOURCE_NAMES]
        if direct_items:
            ordered_items.append(direct_items[0])
        elif category_items:
            ordered_items.append(category_items[0])

    for category in CATEGORIES:
        category_items = category_items_by_name[category]
        for source in DIRECT_SOURCE_NAMES:
            source_items = [item for item in category_items if item.source == source]
            if source_items:
                ordered_items.append(source_items[0])
        ordered_items.extend(item for item in category_items if item.source in DIRECT_SOURCE_NAMES)
        ordered_items.extend(item for item in category_items if item.source not in DIRECT_SOURCE_NAMES)

    for item in ordered_items:
        if consider(item):
            break
    return selected


def fetch_article_image(item: FeedItem) -> str:
    for url in [item.url, item.source_url]:
        image_url = fetch_og_image(url)
        if image_url and not is_unhelpful_thumbnail(image_url):
            return image_url
    return ""


_page_cache: dict[str, str] = {}


def fetch_page(url: str, timeout: int = 12, max_bytes: int = 1_500_000) -> str:
    """1回の実行内で同じURLのHTMLを使い回す（画像取得と本文抽出で二重取得しない）。"""
    if url in _page_cache:
        return _page_cache[url]
    try:
        html_text = fetch_text(url, timeout=timeout, max_bytes=max_bytes)
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError):
        html_text = ""
    _page_cache[url] = html_text
    return html_text


def fetch_article_body(url: str, max_chars: int = 8000) -> str:
    """元記事ページから本文テキストを抽出する。取得できなければ空文字。"""
    html_text = fetch_page(url)
    if not html_text:
        return ""
    parser = ArticleTextParser()
    try:
        parser.feed(html_text)
    except Exception:
        return ""
    # 段落を改行2つで区切って保持（表示側で段落として描画するため）。
    body = "\n\n".join(parser.parts)
    return body[:max_chars]


def fetch_og_image(url: str) -> str:
    if not url:
        return ""
    html_text = fetch_page(url)
    if not html_text:
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


def split_paragraphs(text: str) -> list[str]:
    """改行区切りのテキストを段落リストに分解する（各段落はclean_text済み）。"""
    parts = [clean_text(part) for part in re.split(r"\n+", str(text or ""))]
    return [part for part in parts if part]


def trim_excerpt(text: str, limit: int) -> str:
    """段落の改行を保ったまま指定文字数で切り、切れた場合は「…」を付ける。"""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def build_body(paragraphs: list[str], limit: int, translate: bool) -> str:
    """段落を（必要なら翻訳して）上限文字数まで積み上げ、改行2つで連結する。"""
    if translate:
        source_text = trim_excerpt("\n\n".join(paragraphs), limit)
        return trim_excerpt(translate_to_japanese(source_text), limit)

    collected: list[str] = []
    total = 0
    for para in paragraphs:
        piece = para
        if not piece:
            continue
        collected.append(piece)
        total += len(piece)
        if total >= limit:
            break
    return trim_excerpt("\n\n".join(collected), limit)


def fallback_summary(article: dict[str, Any]) -> dict[str, Any]:
    """Geminiを使わず、本文の抜粋＋元記事リンク方式で記事を組み立てる。

    - 日本語記事: RSS本文をそのまま抜粋。
    - 英語記事: タイトルと本文を無料翻訳して抜粋（トークン消費なし）。
    """
    title = article.get("title", "この記事")
    raw = str(article.get("description", ""))
    translated_title = translate_to_japanese(title) if is_likely_english_title(str(title)) else ""
    paragraphs = split_paragraphs(raw)
    is_en = bool(paragraphs) and needs_japanese_translation(raw)
    body = build_body(paragraphs, EXCERPT_BODY_CHARS, translate=is_en) if paragraphs else ""
    if not body:
        display_title = translated_title or clean_text(title)
        body = f"「{display_title}」に関するニュースです。続きは元記事で確認できます。"
    return {
        "title": make_title_reader_friendly(
            translated_title or clean_text(title),
            str(title),
            str(article.get("source", "")),
        ),
        "summary": trim_excerpt(body, EXCERPT_SUMMARY_CHARS),
        "article_body": body,
        "key_points": [],
        "importance": 3,
        "source": "translated_fallback" if is_en else "fallback",
    }


def is_likely_english(text: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return False
    ascii_letters = sum(ch.isascii() and ch.isalpha() for ch in cleaned)
    japanese_chars = sum("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in cleaned)
    return ascii_letters >= 40 and ascii_letters > japanese_chars * 2


def is_likely_english_title(text: str) -> bool:
    """短い見出しでも英語と判定できるよう、本文より低い文字数基準を使う。"""
    cleaned = clean_text(text)
    if not cleaned:
        return False
    ascii_letters = sum(ch.isascii() and ch.isalpha() for ch in cleaned)
    japanese_chars = sum("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in cleaned)
    return ascii_letters >= 8 and ascii_letters > japanese_chars * 2


def contains_japanese(text: str) -> bool:
    return any("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in clean_text(text))


def needs_japanese_translation(text: str) -> bool:
    """国外記事の短い英文も取りこぼさず、日本語本文は再翻訳しない。"""
    cleaned = clean_text(text)
    return not contains_japanese(cleaned) and (
        is_likely_english(cleaned) or is_likely_english_title(cleaned)
    )


def is_placeholder_summary(text: str) -> bool:
    cleaned = clean_text(text)
    return cleaned.startswith("「") and bool(
        re.search(r"に関する(?:国外)?ニュースです。続きは元記事で確認できます。", cleaned)
    )


def translate_to_japanese(text: str) -> str:
    global translation_disabled_for_run, last_translation_request_at
    source_text = clean_text(text)[:2500]
    if not source_text:
        return ""
    if translation_disabled_for_run:
        return translate_with_mymemory(source_text)
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
    data = None
    for attempt in range(2):
        elapsed = time.monotonic() - last_translation_request_at
        if elapsed < TRANSLATION_REQUEST_INTERVAL:
            time.sleep(TRANSLATION_REQUEST_INTERVAL - elapsed)
        try:
            last_translation_request_at = time.monotonic()
            with urllib.request.urlopen(request, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 0:
                print("Translation rate limit reached. Retrying after 15 seconds.", file=sys.stderr)
                time.sleep(15)
                continue
            if exc.code == 429:
                translation_disabled_for_run = True
                print("Google translation is rate-limited. Using the backup translator.", file=sys.stderr)
                return translate_with_mymemory(source_text)
            return translate_with_mymemory(source_text)
        except (urllib.error.URLError, OSError, TimeoutError, socket.timeout, ValueError, json.JSONDecodeError):
            return translate_with_mymemory(source_text)
    if data is None:
        return ""
    try:
        return clean_text("".join(part[0] for part in data[0] if part and part[0]))
    except (IndexError, TypeError):
        return ""


def translate_with_mymemory(text: str) -> str:
    """Google翻訳が混雑した場合に、無料のMyMemory APIで短い概要を翻訳する。"""
    global last_translation_request_at
    source_bytes = clean_text(text).encode("utf-8")[:450]
    while source_bytes:
        try:
            source_text = source_bytes.decode("utf-8")
            break
        except UnicodeDecodeError:
            source_bytes = source_bytes[:-1]
    else:
        return ""

    elapsed = time.monotonic() - last_translation_request_at
    if elapsed < TRANSLATION_REQUEST_INTERVAL:
        time.sleep(TRANSLATION_REQUEST_INTERVAL - elapsed)
    params = urllib.parse.urlencode({"q": source_text, "langpair": "en|ja", "mt": "1"})
    request = urllib.request.Request(
        f"https://api.mymemory.translated.net/get?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        last_translation_request_at = time.monotonic()
        with urllib.request.urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        if int(data.get("responseStatus", 0)) != 200:
            return ""
        return clean_text(data.get("responseData", {}).get("translatedText", ""))
    except (urllib.error.URLError, OSError, TimeoutError, socket.timeout, ValueError, json.JSONDecodeError):
        return ""


def make_title_reader_friendly(
    translated_title: str, original_title: str = "", source: str = ""
) -> str:
    """直訳調の日本語タイトルを、意味を変えず平易なニュース見出しへ整える。"""
    title = clean_text(translated_title)
    if not title:
        return ""

    # Google Newsなどが見出し末尾へ付ける媒体名は、カード上の媒体欄と重複するため除く。
    cleaned_source = clean_text(source)
    if cleaned_source and title.endswith(cleaned_source):
        title = re.sub(r"\s*(?:-|–|—|｜|\|)\s*" + re.escape(cleaned_source) + r"$", "", title)
    title = re.sub(r"\s*執筆\s*$", "", title).strip()

    # 元から日本語の記事は媒体の見出しを尊重し、英語から翻訳した記事だけを整える。
    if original_title and not is_likely_english_title(original_title):
        return title

    for pattern, replacement in READER_FRIENDLY_TITLE_REPLACEMENTS:
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)

    title = re.sub(r"(\d+(?:\.\d+)?%)\s*の?スコアを獲得", r"\1を達成", title)
    title = re.sub(r"\s+([、。！？：])", r"\1", title)
    title = re.sub(r"([（])\s+", r"\1", title)
    title = re.sub(r"\s+([）])", r"\1", title)
    title = re.sub(r"(?<=[ぁ-んァ-ヶ一-龯])\s+(?=[ぁ-んァ-ヶ一-龯])", "", title)
    title = re.sub(r"\s+(の|を|が|は|に|で|と|へ|から|より)(?=\s|[ぁ-んァ-ヶ一-龯])", r"\1", title)
    title = re.sub(r"\s+(の|を|が|は|に|で|と|へ)(?=、|[ぁ-んァ-ヶ一-龯])", r"\1", title)
    title = re.sub(r"(の|を|が|は|に|で|と|へ)\s+(?=[A-Za-z0-9])", r"\1", title)
    title = re.sub(r"\b(Claude|NVIDIA|OpenAI|Apple|Google|Anthropic)\s+(?=[ぁ-んァ-ヶ一-龯])", r"\1", title)
    title = re.sub(r"(?<=[ぁ-んァ-ヶ一-龯])\s+(?=[A-Za-z0-9])", " ", title)
    title = re.sub(r"\s{2,}", " ", title).strip()

    title = re.sub(r"をリリース(?=$|[、。！？])", "を公開", title)
    title = re.sub(r"スコアを獲得", "好成績を達成", title)
    title = title.replace("すべての新しい噂", "現在わかっている新情報まとめ")
    return title


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


def article_title_key(title: str) -> str:
    return re.sub(r"[^0-9a-zぁ-んァ-ン一-龯]", "", clean_text(title).lower())


def deduplicate_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """同じ見出しの記事は、Google Newsの転送URLより元媒体のURLを残す。"""
    selected: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    preferred = sorted(
        articles,
        key=lambda article: (
            "news.google.com" in str(article.get("url", "")),
            -parse_datetime(article.get("published_at", "")).timestamp(),
        ),
    )
    for article in preferred:
        title_key = article_title_key(article.get("title", ""))
        if title_key and title_key in seen_titles:
            continue
        if title_key:
            seen_titles.add(title_key)
        selected.append(article)
    return sort_articles(selected)


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
