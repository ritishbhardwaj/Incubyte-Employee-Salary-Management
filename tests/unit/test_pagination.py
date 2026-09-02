from app.pagination import clamp_page, offset_for


def test_clamp_page_floors_and_caps() -> None:
    assert clamp_page(0, 0) == (1, 1)
    assert clamp_page(2, 500) == (2, 100)


def test_offset() -> None:
    assert offset_for(1, 25) == 0
    assert offset_for(3, 25) == 50
