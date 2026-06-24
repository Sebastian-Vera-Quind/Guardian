from typing import List, Union
from src.domain.models.util import FileContent


class CodeSanitizer:

    @staticmethod
    def remove_blank_lines(content: str) -> str:
        lines = content.split('\n')
        return '\n'.join(line for line in lines if line.strip())

    @staticmethod
    def _ensure_file_content(file: Union[dict, FileContent]) -> FileContent:
        """Convert dict to FileContent if needed."""
        if isinstance(file, dict):
            return FileContent(**file)
        return file

    @staticmethod
    def sanitize_files(
        files: List[Union[dict, FileContent]]
    ) -> List[FileContent]:
        result = []
        for file in files:
            file_obj = CodeSanitizer._ensure_file_content(file)
            sanitized = CodeSanitizer.remove_blank_lines(file_obj.content)
            if sanitized.strip():
                result.append(FileContent(
                    path=file_obj.path,
                    content=sanitized,
                    extension=file_obj.extension
                ))
        return result

    @staticmethod
    def count_lines(files: List[Union[dict, FileContent]]) -> int:
        return sum(
            len(CodeSanitizer._ensure_file_content(f).content.split('\n'))
            for f in files
        )
