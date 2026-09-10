import re
from collections.abc import Callable

from markupsafe import Markup, escape

CODE_FENCE = "```"
LIST_MARKER = "- "
QUOTE_MARKER = "> "

_HEADING_LEVELS = {"### ": "h3", "## ": "h2"}
_BLOCK_PREFIXES = (CODE_FENCE, *_HEADING_LEVELS, LIST_MARKER, QUOTE_MARKER)
_SAFE_URL_SCHEMES = ("http://", "https://")

_CODE_SPAN = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"\*([^*]+)\*")


def render(raw: str) -> Markup:
    lines = [line.rstrip(" \t") for line in raw.split("\n")]
    html: list[str] = []
    cursor = 0

    while cursor < len(lines):
        cursor = _render_block(html, lines, cursor)

    return Markup("".join(html))


def _render_block(html: list[str], lines: list[str], cursor: int) -> int:
    line = lines[cursor]

    if line.startswith(CODE_FENCE):
        return _render_code_block(html, lines, cursor)

    for prefix, tag in _HEADING_LEVELS.items():
        if line.startswith(prefix):
            html.append(f"<{tag}>{_render_inline(line[len(prefix) :])}</{tag}>\n")
            return cursor + 1

    if line.startswith(LIST_MARKER):
        return _render_list(html, lines, cursor)
    if line.startswith(QUOTE_MARKER):
        return _render_blockquote(html, lines, cursor)
    if not line.strip():
        return cursor + 1

    return _render_paragraph(html, lines, cursor)


def _render_code_block(html: list[str], lines: list[str], cursor: int) -> int:
    body, cursor = _take_while(
        lines, cursor + 1, lambda line: not line.startswith(CODE_FENCE)
    )
    html.append(f"<pre><code>{escape(chr(10).join(body))}</code></pre>\n")

    return cursor + 1 if cursor < len(lines) else cursor


def _render_list(html: list[str], lines: list[str], cursor: int) -> int:
    raw_items, cursor = _take_while(
        lines, cursor, lambda line: line.startswith(LIST_MARKER)
    )
    items = "".join(
        f"<li>{_render_inline(item[len(LIST_MARKER) :])}</li>\n" for item in raw_items
    )
    html.append(f"<ul>\n{items}</ul>\n")

    return cursor


def _render_blockquote(html: list[str], lines: list[str], cursor: int) -> int:
    quoted, cursor = _take_while(
        lines, cursor, lambda line: line.startswith(QUOTE_MARKER)
    )
    text = " ".join(line[len(QUOTE_MARKER) :] for line in quoted)
    html.append(f"<blockquote><p>{_render_inline(text)}</p></blockquote>\n")

    return cursor


def _render_paragraph(html: list[str], lines: list[str], cursor: int) -> int:
    body, cursor = _take_while(lines, cursor, lambda line: not _starts_block(line))
    html.append(f"<p>{_render_inline(' '.join(body))}</p>\n")

    return cursor


def _take_while(
    lines: list[str], cursor: int, keep: Callable[[str], bool]
) -> tuple[list[str], int]:
    start = cursor
    while cursor < len(lines) and keep(lines[cursor]):
        cursor += 1

    return lines[start:cursor], cursor


def _starts_block(line: str) -> bool:
    return not line.strip() or line.startswith(_BLOCK_PREFIXES)


def _render_inline(raw: str) -> str:
    text, code_spans = _extract_code_spans(str(escape(raw)))
    text = _LINK.sub(_replace_link, text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)

    return _restore_code_spans(text, code_spans)


def _extract_code_spans(text: str) -> tuple[str, list[str]]:
    spans: list[str] = []

    def capture(match: re.Match[str]) -> str:
        spans.append(match.group(1))
        return _placeholder(len(spans) - 1)

    return _CODE_SPAN.sub(capture, text), spans


def _restore_code_spans(text: str, spans: list[str]) -> str:
    for index, content in enumerate(spans):
        text = text.replace(_placeholder(index), f"<code>{content}</code>")

    return text


def _placeholder(index: int) -> str:
    return f"\x00{index}\x00"


def _replace_link(match: re.Match[str]) -> str:
    text, url = match.group(1), match.group(2)
    if not _is_safe_url(url):
        return match.group(0)

    return f'<a href="{url}" rel="noopener noreferrer">{text}</a>'


def _is_safe_url(url: str) -> bool:
    if url.lower().startswith(_SAFE_URL_SCHEMES):
        return True

    return url.startswith("/") and not url.startswith("//")
