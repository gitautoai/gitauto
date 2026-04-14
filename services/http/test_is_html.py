# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import Mock

from services.http.is_html import is_html


class TestIsHtml:
    def test_html_content_type(self):
        resp = Mock()
        resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        resp.text = "anything"
        assert is_html(resp) is True

    def test_json_content_type(self):
        resp = Mock()
        resp.headers = {"Content-Type": "application/json"}
        resp.text = '{"key": "value"}'
        assert is_html(resp) is False

    def test_no_content_type_but_html_body(self):
        resp = Mock()
        resp.headers = {}
        resp.text = "<!DOCTYPE html><html><body>Hello</body></html>"
        assert is_html(resp) is True

    def test_no_content_type_plain_text(self):
        resp = Mock()
        resp.headers = {}
        resp.text = "Just plain text content"
        assert is_html(resp) is False
