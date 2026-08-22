import unittest

from fetch_news import make_title_reader_friendly


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


if __name__ == "__main__":
    unittest.main()
