import math
from typing import TypeVar

T = TypeVar("T")


def paginate_items(
    items: list[T],
    page: int = 1,
    page_size: int = 10,
) -> dict:
    total = len(items)
    total_pages = math.ceil(total / page_size)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
    }