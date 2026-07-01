import re

# OWASP LLM01: delimiter tags that signal externally-supplied content.
# The closing tag prevents injected text from "escaping" into the prompt.
_OPEN_TAG = "<user_content>"
_CLOSE_TAG = "</user_content>"

# Control characters that are not printable ASCII (except common whitespace).
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def wrap_user_content(content: str) -> str:
  """Wrap externally-sourced content in delimiters to prevent prompt
  injection (OWASP LLM01).

  The delimiters signal to the downstream LLM that the enclosed text is
  user/external data and must not be interpreted as system instructions.

  Args:
    content: Raw text from a DB chunk, file, or similar external source.

  Returns:
    String with opening and closing tags around the content.
  """
  return f"{_OPEN_TAG}\n{content}\n{_CLOSE_TAG}"


def escape_for_prompt(text: str) -> str:
  """Escape special sequences that could break prompt structure.

  Replaces characters that LLMs may interpret as role-change markers
  or instruction delimiters.

  Args:
    text: Text to sanitize before inserting into a prompt.

  Returns:
    Text with dangerous sequences replaced by safe equivalents.
  """
  text = text.replace("###", "[HASH]")
  text = text.replace("```", "[FENCE]")
  text = text.replace("<|", "[LANGLE_PIPE]")
  text = text.replace("|>", "[PIPE_RANGLE]")
  return text


def sanitize_file_content(content: str) -> str:
  """Remove non-printable control characters from file content.

  Strips invisible characters that could be used as injection vectors
  embedded in source files processed by the RAG pipeline.

  Args:
    content: Raw file content string.

  Returns:
    Cleaned content with control characters removed.
  """
  return _CONTROL_CHARS_RE.sub("", content)
