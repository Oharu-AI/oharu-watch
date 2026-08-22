"""Gemini-based article summarization for OHARU WATCH.

The rest of the app calls summarize_article() so the model provider can be
changed later without rewriting the RSS collection flow.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash-lite"
FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
MAX_ATTEMPTS_PER_MODEL = 1
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}


class SummarizerError(RuntimeError):
    """Raised when Gemini cannot return a usable summary."""


class GeminiHttpError(SummarizerError):
    """Raised when Gemini returns an HTTP error."""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"Gemini API HTTP {status_code}: {body}")
        self.status_code = status_code
        self.body = body


def summarize_article(article: dict[str, Any]) -> dict[str, Any]:
    """Return summary, key_points, and importance for an article.

    The GEMINI_API_KEY environment variable must be available in production.
    """

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SummarizerError("GEMINI_API_KEY is not set.")

    preferred_model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    models = unique_models([preferred_model, *FALLBACK_MODELS])
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": build_prompt(article),
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    errors: list[str] = []
    for model in models:
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                raw_response = request_gemini(api_key, model, payload)
                response_data = json.loads(raw_response)
                text = extract_text(response_data)
                summary_data = parse_json_text(text)
                return normalize_summary(summary_data)
            except GeminiHttpError as exc:
                errors.append(f"{model} attempt {attempt}: HTTP {exc.status_code}")
                if exc.status_code in RETRYABLE_HTTP_CODES and attempt < MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(2 * attempt)
                    continue
                if exc.status_code in RETRYABLE_HTTP_CODES:
                    break
                raise

    raise SummarizerError("Gemini summarization failed after retries: " + "; ".join(errors))


def request_gemini(api_key: str, model: str, payload: dict[str, Any]) -> str:
    request = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise GeminiHttpError(exc.code, error_body) from exc
    except urllib.error.URLError as exc:
        raise SummarizerError(f"Gemini API request failed: {exc}") from exc


def build_prompt(article: dict[str, Any]) -> str:
    title = clean_text(article.get("title", ""))
    category = clean_text(article.get("category", ""))
    source = clean_text(article.get("source", ""))
    description = clean_text(article.get("description", "") or article.get("summary", ""))
    url = clean_text(article.get("url", ""))

    return f"""
あなたは個人用ニュースダッシュボード「OHARU WATCH」の編集者です。
以下の記事情報だけを使い、日本語で短く実用的に要約してください。

返答はJSONのみ。Markdown、コードブロック、補足文は禁止です。

JSON形式:
{{
  "title": "非エンジニアにも内容が一読で分かる、自然な日本語の記事タイトル。",
  "summary": "詳細ページ向けの要約。300〜450字程度。",
  "article_body": "記事の内容を500〜800字程度で説明。全文転載ではなく、記事情報から分かる範囲の整理。",
  "key_points": ["重要ポイント1", "重要ポイント2", "重要ポイント3"],
  "importance": 1
}}

ルール:
- article_bodyは元記事の全文転載ではなく、読者が内容を把握できる詳しい説明にする。
- titleは必ず日本語で返す。英語タイトルは直訳せず、製品名・企業名・数値・事実を保ったまま、非エンジニアにも何が起きたか分かるニュース見出しにする。
- benchmarkは「性能テスト」、coding agentは「プログラミング支援AI」のように、専門用語は短い平易な言葉へ置き換える。意味を断定できない用語は無理に言い換えない。
- key_pointsは必ず3つ。
- importanceは1〜5の整数。5が最重要。
- 誇張せず、記事情報から分かる範囲だけを書く。
- OpenAI、ChatGPT、Anthropic、Claude、Google AIの技術・プロダクト・業界影響が分かるように書く。
- 「私への影響」は生成しない。

記事:
タイトル: {title}
カテゴリ: {category}
ソース: {source}
RSS概要: {description}
URL: {url}
""".strip()


def unique_models(models: list[str]) -> list[str]:
    seen = set()
    unique = []
    for model in models:
        normalized = model.strip()
        if normalized and normalized not in seen:
            unique.append(normalized)
            seen.add(normalized)
    return unique


def extract_text(response_data: dict[str, Any]) -> str:
    try:
        parts = response_data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SummarizerError(f"Gemini response has no text: {response_data}") from exc

    text_parts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    text = "\n".join(part for part in text_parts if part).strip()
    if not text:
        raise SummarizerError(f"Gemini response text is empty: {response_data}")
    return text


def parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise SummarizerError(f"Gemini returned invalid JSON: {text}") from exc

    if not isinstance(data, dict):
        raise SummarizerError(f"Gemini JSON must be an object: {data}")
    return data


def normalize_summary(data: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(data.get("title", ""))
    summary = clean_text(data.get("summary", ""))
    article_body = clean_text(data.get("article_body", ""))
    key_points = data.get("key_points", [])
    importance = data.get("importance", 3)

    if not summary:
        raise SummarizerError("Gemini summary is empty.")
    if not article_body:
        article_body = summary

    if not isinstance(key_points, list):
        key_points = []
    normalized_points = [clean_text(point) for point in key_points if clean_text(point)]
    normalized_points = normalized_points[:3]
    while len(normalized_points) < 3:
        normalized_points.append("記事本文の追加確認が必要です。")

    try:
        normalized_importance = int(importance)
    except (TypeError, ValueError):
        normalized_importance = 3
    normalized_importance = max(1, min(5, normalized_importance))

    return {
        "title": title,
        "summary": summary,
        "article_body": article_body,
        "key_points": normalized_points,
        "importance": normalized_importance,
        "source": "gemini",
    }


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
