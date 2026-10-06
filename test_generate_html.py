import base64
import hashlib
import re
import unittest

from generate_html import add_security_meta, article_image, render_article_page, safe_image_url


class SecurityMetaTest(unittest.TestCase):
    def test_csp_allows_only_the_pages_own_inline_scripts(self):
        script = "\n  console.log('ok');\n"
        page = f'<!doctype html><html><head>\n  <meta charset="utf-8">\n</head><body><script>{script}</script></body></html>'
        result = add_security_meta(page)

        digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
        self.assertIn(f"script-src &#x27;sha256-{digest}&#x27;", result)
        self.assertIn("object-src &#x27;none&#x27;", result)
        self.assertIn("base-uri &#x27;none&#x27;", result)
        self.assertNotIn("unsafe-inline", result)
        self.assertNotIn("unsafe-eval", result)
        self.assertLess(result.index("Content-Security-Policy"), result.index("<script>"))

    def test_json_data_block_is_not_treated_as_executable_script(self):
        page = '<meta charset="utf-8"><script id="d" type="application/json">{}</script>'
        self.assertIn("script-src &#x27;none&#x27;", add_security_meta(page))


class ArticlePageInjectionTest(unittest.TestCase):
    def test_script_tags_in_article_text_cannot_break_out_of_the_data_block(self):
        evil = {
            "id": "x",
            "title": "</script><script>alert(1)</script><!--",
            "category": "AI最新情報（国内）",
            "article_body": "<script>alert(2)</script>",
            "url": "https://example.com/",
        }
        page = add_security_meta(render_article_page([evil]))
        # 実行されるインラインscriptは、ページ自身のもの1つだけ（記事由来のscriptが増えていない）。
        self.assertEqual(len(re.findall(r"<script>", page)), 1)
        self.assertEqual(len(re.findall(r"</script>", page)), 2)  # データ用 + ページ自身
        self.assertNotIn("</script><script>alert", page)


class ImageUrlTest(unittest.TestCase):
    def test_only_http_and_local_assets_are_allowed(self):
        self.assertEqual(safe_image_url("https://example.com/a.png"), "https://example.com/a.png")
        self.assertEqual(safe_image_url("assets/default-ai.png"), "assets/default-ai.png")
        for bad in ["javascript:alert(1)", "data:image/svg+xml,<svg onload=alert(1)>", "file:///etc/passwd", "//evil.example/x.png", ""]:
            self.assertEqual(safe_image_url(bad), "", bad)

    def test_unsafe_thumbnail_falls_back_to_category_default(self):
        article = {"category": "AI最新情報（国内）", "thumbnail_url": "javascript:alert(1)"}
        self.assertEqual(article_image(article), "assets/default-ai.png")


if __name__ == "__main__":
    unittest.main()
