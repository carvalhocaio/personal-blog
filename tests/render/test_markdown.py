import pytest
from markupsafe import Markup

from personal_blog.render.markdown import render


class TestBlocks:
    def test_renders_level_two_heading(self) -> None:
        assert render("## Cost Cap") == "<h2>Cost Cap</h2>\n"

    def test_renders_level_three_heading(self) -> None:
        assert render("### Wind Tunnel Time") == "<h3>Wind Tunnel Time</h3>\n"

    def test_joins_consecutive_lines_into_one_paragraph(self) -> None:
        assert render("first line\nsecond line") == "<p>first line second line</p>\n"

    def test_blank_line_starts_a_new_paragraph(self) -> None:
        assert render("first\n\nsecond") == "<p>first</p>\n<p>second</p>\n"

    def test_renders_unordered_list(self) -> None:
        raw = "- Driver salaries\n- Marketing costs"

        assert (
            render(raw)
            == "<ul>\n<li>Driver salaries</li>\n<li>Marketing costs</li>\n</ul>\n"
        )

    def test_renders_blockquote_as_a_single_paragraph(self) -> None:
        assert (
            render("> first\n> second")
            == "<blockquote><p>first second</p></blockquote>\n"
        )

    def test_a_block_ends_the_paragraph_before_it(self) -> None:
        assert render("intro\n## Heading") == "<p>intro</p>\n<h2>Heading</h2>\n"

    def test_renders_nothing_for_empty_content(self) -> None:
        assert render("") == ""

    def test_returns_markup(self) -> None:
        assert isinstance(render("body"), Markup)


class TestCodeBlocks:
    def test_renders_fenced_code_block(self) -> None:
        assert render("```\nmake seed\n```") == "<pre><code>make seed</code></pre>\n"

    def test_preserves_line_breaks_inside_the_block(self) -> None:
        raw = "```\nfirst\nsecond\n```"

        assert render(raw) == "<pre><code>first\nsecond</code></pre>\n"

    def test_ignores_the_info_string(self) -> None:
        assert render("```python\npass\n```") == "<pre><code>pass</code></pre>\n"

    def test_keeps_markdown_syntax_literal(self) -> None:
        assert (
            render("```\n**not bold**\n```") == "<pre><code>**not bold**</code></pre>\n"
        )

    def test_escapes_html_inside_the_block(self) -> None:
        assert (
            render("```\n<script>\n```") == "<pre><code>&lt;script&gt;</code></pre>\n"
        )

    def test_closes_an_unterminated_block(self) -> None:
        assert render("```\nmake run") == "<pre><code>make run</code></pre>\n"


class TestInlineFormatting:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("a **cost cap** rule", "<p>a <strong>cost cap</strong> rule</p>\n"),
            ("a *deliberate* choice", "<p>a <em>deliberate</em> choice</p>\n"),
            ("run `make seed` first", "<p>run <code>make seed</code> first</p>\n"),
        ],
    )
    def test_applies_inline_markers(self, raw: str, expected: str) -> None:
        assert render(raw) == expected

    def test_applies_inline_markers_inside_headings(self) -> None:
        assert (
            render("## The **Cost Cap**") == "<h2>The <strong>Cost Cap</strong></h2>\n"
        )

    def test_applies_inline_markers_inside_list_items(self) -> None:
        assert (
            render("- a *deliberate* choice")
            == "<ul>\n<li>a <em>deliberate</em> choice</li>\n</ul>\n"
        )

    def test_code_spans_shield_markdown_syntax(self) -> None:
        assert render("`**not bold**`") == "<p><code>**not bold**</code></p>\n"

    def test_code_spans_escape_their_content(self) -> None:
        assert render("`<b>`") == "<p><code>&lt;b&gt;</code></p>\n"


class TestLinks:
    @pytest.mark.parametrize(
        "url",
        [
            "https://roadmap.sh/projects/personal-blog",
            "http://example.com",
            "HTTPS://example.com",
            "/articles/trench",
        ],
    )
    def test_renders_safe_urls_as_anchors(self, url: str) -> None:
        expected = f'<p><a href="{url}" rel="noopener noreferrer">link</a></p>\n'

        assert render(f"[link]({url})") == expected

    @pytest.mark.parametrize(
        "url",
        [
            "javascript:alert(1)",
            "data:text/html,<script>",
            "vbscript:msgbox",
            "//evil.example.com",
        ],
    )
    def test_leaves_unsafe_urls_as_inert_text(self, url: str) -> None:
        rendered = render(f"[link]({url})")

        assert "<a" not in rendered
        assert "href" not in rendered


class TestEscaping:
    def test_escapes_html_in_paragraphs(self) -> None:
        rendered = render("<script>alert('x')</script>")

        assert "<script>" not in rendered
        assert "&lt;script&gt;" in rendered

    def test_escapes_html_in_headings(self) -> None:
        assert "<img" not in render("## <img src=x onerror=alert(1)>")

    def test_escapes_html_in_list_items(self) -> None:
        assert "<iframe" not in render("- <iframe src=evil>")

    def test_escapes_html_in_blockquotes(self) -> None:
        assert "<script>" not in render("> <script>alert(1)</script>")

    def test_escapes_ampersands(self) -> None:
        assert render("Red Bull & Ferrari") == "<p>Red Bull &amp; Ferrari</p>\n"

    def test_markdown_emphasis_cannot_smuggle_html(self) -> None:
        assert (
            render("**<b>bold</b>**")
            == "<p><strong>&lt;b&gt;bold&lt;/b&gt;</strong></p>\n"
        )
