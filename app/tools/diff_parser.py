import re

from app.schemas.pr_models import AddedLine, DiffHunk

HUNK_RE = re.compile(r"^@@ -(?:\d+)(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_patch(patch: str) -> list[DiffHunk]:
    if not patch:
        return []

    hunks: list[DiffHunk] = []
    current_hunk: DiffHunk | None = None
    new_line = 0

    for raw_line in patch.splitlines():
        header = HUNK_RE.match(raw_line)
        if header:
            start_line = int(header.group(1))
            current_hunk = DiffHunk(start_line=start_line, end_line=start_line, added_lines=[])
            hunks.append(current_hunk)
            new_line = start_line
            continue

        if current_hunk is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            current_hunk.added_lines.append(AddedLine(line_number=new_line, content=raw_line[1:]))
            current_hunk.end_line = new_line
            new_line += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            continue
        else:
            current_hunk.end_line = max(current_hunk.end_line, new_line)
            new_line += 1

    return hunks


def extract_changed_lines(patch: str) -> list[int]:
    changed: list[int] = []
    for hunk in parse_patch(patch):
        changed.extend(line.line_number for line in hunk.added_lines)
    return changed


def extract_added_lines(patch: str) -> list[AddedLine]:
    added: list[AddedLine] = []
    for hunk in parse_patch(patch):
        added.extend(hunk.added_lines)
    return added