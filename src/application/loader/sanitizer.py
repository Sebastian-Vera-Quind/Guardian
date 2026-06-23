from typing import List
from src.domain.models.state.file import FileContent


class CodeSanitizer:

    @staticmethod
    def remove_blank_lines(content: str) -> str:
        lines = content.split('\n')
        return '\n'.join(line for line in lines if line.strip())

    @staticmethod
    def sanitize_files(files: List[FileContent]) -> List[FileContent]:
        result = []
        for file in files:
            sanitized = CodeSanitizer.remove_blank_lines(file["content"])
            if sanitized.strip():
                result.append(FileContent(
                    path=file["path"],
                    content=sanitized,
                    extension=file["extension"]
                ))
        return result

    @staticmethod
    def count_lines(files: List[FileContent]) -> int:
        return sum(len(f["content"].split('\n')) for f in files)
