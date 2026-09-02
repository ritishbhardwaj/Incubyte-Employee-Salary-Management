def clamp_page(page: int, page_size: int, *, max_size: int = 100) -> tuple[int, int]:
    page = max(int(page), 1)
    page_size = min(max(int(page_size), 1), max_size)
    return page, page_size


def offset_for(page: int, page_size: int) -> int:
    return (page - 1) * page_size
