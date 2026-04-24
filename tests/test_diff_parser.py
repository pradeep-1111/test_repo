from app.tools.diff_parser import extract_added_lines, extract_changed_lines, parse_patch


PATCH = """@@ -1,2 +1,3 @@\n line1\n-line2\n+line2_changed\n+line3\n"""


def test_diff_parser_extracts_changed_lines() -> None:
    assert extract_changed_lines(PATCH) == [2, 3]
    assert [item.content for item in extract_added_lines(PATCH)] == ["line2_changed", "line3"]
    assert len(parse_patch(PATCH)) == 1