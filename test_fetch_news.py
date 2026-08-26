import unittest
import socket
from unittest.mock import patch

from fetch_news import (
    FeedItem,
    fallback_summary,
    make_title_reader_friendly,
    refresh_global_summaries_from_feeds,
    refresh_local_translations,
    translate_with_mymemory,
)


class ReaderFriendlyTitleTest(unittest.TestCase):
    def test_replaces_ai_jargon_without_changing_product_or_score(self):
        title = "NVIDIA のコーディング エージェントは、ARC-AGI-3 インタラクティブ推論ベンチマークで 100% のスコアを獲得"
        original = "NVIDIA's coding agent scored 100% on the ARC-AGI-3 interactive reasoning benchmark"

        self.assertEqual(
            make_title_reader_friendly(title, original),
            "NVIDIAのプログラミング支援AIは、ARC-AGI-3 対話型の推論能力テストで100%を達成",
        )

    def test_explains_opaque_technical_term(self):
        title = "Nvidia は、AI モデルではなくハーネスが本当の主役だと示した"
        original = "Nvidia showed that the harness, not the AI model, is the real hero"

        self.assertEqual(
            make_title_reader_friendly(title, original),
            "Nvidiaは、AIモデルではなくAIを実際に動かす仕組みが本当の主役だと示した",
        )

    def test_keeps_original_japanese_headline(self):
        title = "AIエージェントの性能を検証、国内企業が新サービス"

        self.assertEqual(make_title_reader_friendly(title, title), title)

    def test_removes_repeated_google_news_source_suffix(self):
        title = "Anthropicが元Googleチップ責任者を採用 執筆 - Investing.com"

        self.assertEqual(
            make_title_reader_friendly(title, title, "Investing.com"),
            "Anthropicが元Googleチップ責任者を採用",
        )

    def test_is_idempotent(self):
        title = "Claude のプログラミング支援AIが性能テストで首位"
        original = "Claude coding agent tops benchmark"
        once = make_title_reader_friendly(title, original)

        self.assertEqual(make_title_reader_friendly(once, original), once)

    def test_rewords_security_jargon_as_an_action(self):
        title = "クロード サブエージェントがプロンプトを挿入しました"
        original = "Claude subagent performed a prompt injection"

        self.assertEqual(
            make_title_reader_friendly(title, original),
            "Claude補助AIが悪意ある指示を紛れ込ませました",
        )


class GlobalArticleTranslationTest(unittest.TestCase):
    @patch("fetch_news.time.sleep")
    @patch("fetch_news.translate_to_japanese")
    def test_translates_global_title_and_summary_even_when_gemini_is_source(self, translate, _sleep):
        translate.side_effect = {
            "OpenAI launches a new model": "OpenAIが新しいAIモデルを発表",
            "The model is faster and uses less memory.": "新モデルは高速で、使用メモリも少なくなっています。",
        }.get
        article = {
            "title": "OpenAI launches a new model",
            "summary": "The model is faster and uses less memory.",
            "article_body": "The model is faster and uses less memory.",
            "category": "AI最新情報（国外）",
            "summary_source": "gemini",
        }

        translated = refresh_local_translations([article])[0]

        self.assertEqual(translated["title"], "OpenAIが新しいAIモデルを発表")
        self.assertEqual(translated["summary"], "新モデルは高速で、使用メモリも少なくなっています。")
        self.assertEqual(translated["article_body"], translated["summary"])

    @patch("fetch_news.time.sleep")
    @patch("fetch_news.translate_to_japanese", return_value="AIへの指示は次の通りでした")
    def test_rebuilds_mixed_language_placeholder_with_translated_title(self, _translate, _sleep):
        article = {
            "title": "AI prompt was:",
            "summary": "「AI prompt was:」に関するニュースです。続きは元記事で確認できます。",
            "article_body": "「AI prompt was:」に関するニュースです。続きは元記事で確認できます。",
            "category": "AI最新情報（国外）",
            "summary_source": "fallback",
        }

        translated = refresh_local_translations([article])[0]

        self.assertEqual(translated["title"], "AIへの指示は次の通りでした")
        self.assertEqual(
            translated["summary"],
            "「AIへの指示は次の通りでした」に関する国外ニュースです。続きは元記事で確認できます。",
        )

    @patch("fetch_news.translate_to_japanese", return_value="新しいAIモデルを発表")
    def test_new_global_article_uses_translated_title_in_fallback_summary(self, _translate):
        result = fallback_summary(
            {
                "title": "Introducing a new AI model",
                "description": "",
                "category": "AI最新情報（国外）",
                "source": "Example",
            }
        )

        self.assertEqual(result["title"], "新しいAIモデルを発表")
        self.assertIn("新しいAIモデルを発表", result["summary"])
        self.assertNotIn("Introducing a new AI model", result["summary"])

    @patch("fetch_news.translate_to_japanese", return_value="新モデルは処理速度と省メモリ性能を改善しました。")
    def test_replaces_placeholder_with_feed_summary_when_feed_is_seen_again(self, _translate):
        article = {
            "url": "https://example.com/new-model",
            "title": "新しいAIモデルを発表",
            "summary": "「新しいAIモデルを発表」に関する国外ニュースです。続きは元記事で確認できます。",
            "article_body": "「新しいAIモデルを発表」に関する国外ニュースです。続きは元記事で確認できます。",
            "category": "AI最新情報（国外）",
        }
        item = FeedItem(
            title="Introducing a new AI model",
            category="AI最新情報（国外）",
            source="Example",
            source_url="https://example.com",
            published_at="2026-08-24T00:00:00+00:00",
            url="https://example.com/new-model",
            description="The new model improves processing speed and memory efficiency.",
        )

        refreshed = refresh_global_summaries_from_feeds([article], [item])[0]

        self.assertEqual(refreshed["summary"], "新モデルは処理速度と省メモリ性能を改善しました。")
        self.assertEqual(refreshed["description"], item.description)

    @patch("fetch_news.time.sleep")
    @patch("fetch_news.urllib.request.urlopen", side_effect=socket.timeout("timed out"))
    def test_backup_translation_timeout_does_not_stop_update(self, _urlopen, _sleep):
        self.assertEqual(translate_with_mymemory("A short English summary."), "")

    @patch("fetch_news.time.sleep")
    @patch("fetch_news.urllib.request.urlopen", side_effect=ConnectionResetError("reset"))
    def test_backup_translation_connection_reset_does_not_stop_update(self, _urlopen, _sleep):
        self.assertEqual(translate_with_mymemory("Another English summary."), "")


if __name__ == "__main__":
    unittest.main()
