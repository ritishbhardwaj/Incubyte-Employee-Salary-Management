from app.core.csrf import origin_is_allowed, tokens_match


def test_tokens_must_match_exactly() -> None:
    assert tokens_match("abc", "abc")
    assert not tokens_match("abc", "abd")
    assert not tokens_match(None, "abc")
    assert not tokens_match("abc", None)


def test_origin_allowlist() -> None:
    allowed = ["http://localhost:5173", "http://testserver"]
    assert origin_is_allowed("http://testserver", allowed)
    assert not origin_is_allowed("https://evil.example", allowed)
    assert not origin_is_allowed(None, allowed)
