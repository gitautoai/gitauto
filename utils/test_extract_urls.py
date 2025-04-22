import unittest
from utils.extract_urls import extract_image_urls, extract_urls


class TestExtractUrls(unittest.TestCase):
    def test_extract_image_urls_excludes_svg(self):
        text = '<img alt="Image one" src="http://example.com/image.png"><img alt="Vector" src="http://example.com/vector.svg">'
        result = extract_image_urls(text)
        expected = [{"alt": "Image one", "url": "http://example.com/image.png"}]
        self.assertEqual(result, expected)

    def test_extract_image_urls_multiple(self):
        text = ('<img alt="first" src="http://example.com/first.jpg">'
                '<img alt="second" src="http://example.com/second.jpeg">'
                '<img alt="third" src="http://example.com/third.svg">')
        result = extract_image_urls(text)
        expected = ([{"alt": "first", "url": "http://example.com/first.jpg"},
                     {"alt": "second", "url": "http://example.com/second.jpeg"}])
        self.assertEqual(result, expected)

    def test_extract_image_urls_no_images(self):
        text = 'No image tags here'
        result = extract_image_urls(text)
        self.assertEqual(result, [])

    def test_extract_urls_empty(self):
        text = 'No urls here'
        github_urls, other_urls = extract_urls(text)
        self.assertEqual(github_urls, [])
        self.assertEqual(other_urls, [])

    def test_extract_urls_with_github_and_other(self):
        github_url = "https://github.com/gitautoai/gitauto/blob/main/utils/extract_urls.py"
        other_url = "https://example.com/page"
        text = f"Check this: {github_url} and also {other_url}"
        github, others = extract_urls(text)
        self.assertEqual(github, [github_url])
        self.assertEqual(others, [other_url])

    def test_extract_urls_trailing_line_numbers(self):
        url_with_line = "https://github.com/gitautoai/gitauto/blob/main/utils/extract_urls.py#L10-L20"
        text = f"{url_with_line}"
        github, others = extract_urls(text)
        self.assertEqual(github, [url_with_line])
        self.assertEqual(others, [])

    def test_extract_urls_with_similar_non_github_url(self):
        similar_url = "https://github.com/gitautoai/gitauto/main/utils/extract_urls.py"
        text = similar_url
        github, others = extract_urls(text)
        self.assertEqual(github, [])
        self.assertEqual(others, [similar_url])

if __name__ == '__main__':
    unittest.main()
