# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from services.http.strip_html import strip_html


class TestStripHtml:
    def test_removes_style_and_script_blocks(self):
        html = "<style>.foo{color:red}</style><p>Hello</p><script>alert(1)</script>"
        result = strip_html(html)
        assert "color:red" not in result
        assert "alert" not in result
        assert "Hello" in result

    def test_removes_tags_preserves_text(self):
        html = "<div><p>Hello <b>World</b></p></div>"
        result = strip_html(html)
        assert result == "Hello World"

    def test_collapses_blank_lines(self):
        html = "<div>A</div>\n\n\n<div>B</div>"
        result = strip_html(html)
        assert "\n\n" not in result

    def test_large_css_stripped(self):
        # Simulate real-world: 50K of CSS + small body
        css = "<style>" + ".cls{" + "a:b;" * 5000 + "}</style>"
        html = f"<html><head>{css}</head><body>Content here</body></html>"
        result = strip_html(html)
        assert len(result) < 200
        assert "Content here" in result
