from utils.file_manager import correct_hunk_headers


def test_correct_hunk_headers_1() -> None:
    """Test the case where line counts are wrong"""
    diff_text = """--- a/example.txt
+++ b/example.txt
@@ -1,3 +1,3 @@
- old line 1
+ new line 1
- old line 2
+ new line 2"""
    expected_result = """--- a/example.txt
+++ b/example.txt
@@ -1,2 +1,2 @@
- old line 1
+ new line 1
- old line 2
+ new line 2"""
    assert correct_hunk_headers(diff_text=diff_text) == expected_result


def test_correct_hunk_headers_2() -> None:
    """Test the case where the hunk header does not have a line count"""
    diff_text = """--- a/example2.txt
+++ b/example2.txt
@@ -1 +1 @@
- old line 1
+ new line 1"""
    expected_result = """--- a/example2.txt
+++ b/example2.txt
@@ -1,1 +1,1 @@
- old line 1
+ new line 1"""
    assert correct_hunk_headers(diff_text=diff_text) == expected_result
