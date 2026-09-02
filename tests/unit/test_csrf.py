from types import SimpleNamespace

from app.core.security import origin_from_referer, origin_is_allowed, public_origin, tokens_match


def test_tokens_must_match_exactly() -> None:
    assert tokens_match("abc", "abc")
    assert not tokens_match("abc", "abd")
    assert not tokens_match(None, "abc")
    assert not tokens_match("abc", None)


def test_origin_allowlist() -> None:
    allowed = ["http://localhost:5173", "http://testserver"]
    assert origin_is_allowed("http://testserver", allowed)
    assert origin_is_allowed("http://testserver/", allowed)
    assert not origin_is_allowed("https://evil.example", allowed)
    assert not origin_is_allowed(None, allowed)


def test_same_origin_is_allowed_without_allowlist() -> None:
    cloud = "https://incubyteesm.fastapicloud.dev"
    assert origin_is_allowed(cloud, [], same_origin=cloud)
    assert origin_is_allowed(cloud + "/", [], same_origin=cloud)
    assert not origin_is_allowed("https://evil.example", [], same_origin=cloud)


def test_origin_from_referer() -> None:
    assert origin_from_referer("https://incubyteesm.fastapicloud.dev/employees") == (
        "https://incubyteesm.fastapicloud.dev"
    )
    assert origin_from_referer(None) is None


def test_public_origin_prefers_forwarded_host() -> None:
    request = SimpleNamespace(
        headers={
            "x-forwarded-proto": "https",
            "x-forwarded-host": "incubyteesm.fastapicloud.dev",
            "host": "internal:8080",
        },
        url=SimpleNamespace(scheme="http"),
    )
    assert public_origin(request) == "https://incubyteesm.fastapicloud.dev"
