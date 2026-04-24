import fnmatch
import re

from app.schemas.pr_models import AddedLine


def path_matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def added_lines_matching_pattern(added_lines: list[AddedLine], pattern: str) -> list[AddedLine]:
    regex = re.compile(pattern)
    return [line for line in added_lines if regex.search(line.content)]