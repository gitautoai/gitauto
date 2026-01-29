from utils.formatting.collapse_list import collapse_list


def test_empty_list():
    expected = ""
    assert collapse_list([]) == expected


def test_single_item():
    expected = "- a"
    assert collapse_list(["a"]) == expected


def test_under_max():
    expected = """- a
- b
- c"""
    assert collapse_list(["a", "b", "c"]) == expected


def test_at_max():
    expected = """- a
- b
- c
- d
- e
- f"""
    assert collapse_list(["a", "b", "c", "d", "e", "f"]) == expected


def test_over_max():
    expected = """- a
- b
- c
- ... (1 more items) ...
- e
- f
- g"""
    assert collapse_list(["a", "b", "c", "d", "e", "f", "g"]) == expected


def test_many_items():
    expected = """- 1
- 2
- 3
- ... (4 more items) ...
- 8
- 9
- 10"""
    assert (
        collapse_list(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]) == expected
    )


def test_custom_max():
    expected = """- a
- ... (2 more items) ...
- d"""
    assert collapse_list(["a", "b", "c", "d"], max_items=2) == expected
