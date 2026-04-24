def looks_like_test_file(path: str) -> bool:
    lowered = path.lower()
    return (
        "/test" in lowered
        or "/tests" in lowered
        or lowered.startswith("test")
        or lowered.endswith("_test.py")
        or lowered.endswith(".spec.ts")
        or lowered.endswith(".test.ts")
        or lowered.endswith(".spec.js")
        or lowered.endswith(".test.js")
    )