from pydantic import BaseModel


class ImportRowFailure(BaseModel):
    row: int
    errors: list[str]


class ImportResult(BaseModel):
    created: int
    failed: list[ImportRowFailure]
    total_rows: int
