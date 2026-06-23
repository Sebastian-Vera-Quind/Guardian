from typing import TypedDict


class FileContent(TypedDict):
    path: str
    content: str
    extension: str
