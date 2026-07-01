from typing import List


def build_rag_query(
  contents: List[str],
  char_limit: int = 8000,
  per_file: int = 500,
) -> str:
  """Build a RAG query string from a list of content strings.

  Each element is sliced to at most `per_file` characters; the resulting
  parts are joined with newlines and the total is capped at `char_limit`.
  Returns an empty string when there is no usable content.

  Args:
    contents: List of raw content strings (file contents or diff lines).
    char_limit: Maximum total characters in the returned query.
    per_file: Maximum characters taken from each individual element.

  Returns:
    Concatenated query string, or "" if input is empty or all-blank.
  """
  parts: List[str] = []
  for item in contents:
    chunk = item[:per_file]
    if chunk.strip():
      parts.append(chunk)

  if not parts:
    return ""

  return "\n".join(parts)[:char_limit]
