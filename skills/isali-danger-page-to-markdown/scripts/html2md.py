"""Minimal HTML → Markdown converter (stdlib only).

Target: clean adapter-extracted body HTML (already noise-stripped) → readable
markdown. Not a general-purpose converter — assumes well-formed input.

Handled tags: h1-h6, p, br, hr, a, img, strong/b, em/i, code, pre, ul, ol, li,
blockquote, table (basic). Unknown tags act as transparent containers.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

VOID_TAGS = {"br", "hr", "img"}
INLINE_TAGS = {"a", "strong", "b", "em", "i", "code", "span"}


class _HtmlToMd(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.list_stack: list[tuple[str, int]] = []  # (kind, counter)
        self.blockquote_depth = 0
        self.heading_level = 0
        self.in_pre = 0
        self.in_code = 0
        self.in_a: list[str] = []  # href stack
        self.skip_depth = 0
        self.last_was_block_break = True  # avoid leading blank lines

    # ---- helpers ----
    def emit(self, s: str) -> None:
        if not s:
            return
        if self.skip_depth > 0:
            return
        if not self.in_pre:
            # collapse whitespace runs (but keep newlines as-is for blocks)
            s = re.sub(r"[ \t]+", " ", s)
        self.parts.append(s)
        self.last_was_block_break = False

    def block_break(self) -> None:
        if self.last_was_block_break:
            return
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")
        self.parts.append("\n")
        self.last_was_block_break = True

    def line_break(self) -> None:
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")
        self.last_was_block_break = False

    # ---- handlers ----
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag in ("script", "style", "noscript", "head", "iframe", "form", "nav", "aside", "header", "footer"):
            self.skip_depth += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.block_break()
            self.heading_level = int(tag[1])
            self.emit("#" * self.heading_level + " ")
            return
        if tag == "p":
            self.block_break()
            return
        if tag == "br":
            self.line_break()
            return
        if tag == "hr":
            self.block_break()
            self.emit("---")
            self.block_break()
            return
        if tag in ("strong", "b"):
            self.emit("**")
            return
        if tag in ("em", "i"):
            self.emit("*")
            return
        if tag == "code" and not self.in_pre:
            self.in_code += 1
            self.emit("`")
            return
        if tag == "pre":
            self.block_break()
            self.in_pre += 1
            self.emit("```\n")
            return
        if tag == "a":
            href = (a.get("href") or "").strip()
            self.in_a.append(href)
            self.emit("[")
            return
        if tag == "img":
            src = (a.get("src") or "").strip()
            alt = (a.get("alt") or "").strip()
            if src:
                self.emit(f"![{alt}]({src})")
            return
        if tag == "ul":
            self.block_break()
            self.list_stack.append(("ul", 0))
            return
        if tag == "ol":
            self.block_break()
            self.list_stack.append(("ol", 0))
            return
        if tag == "li":
            self.line_break()
            depth = max(0, len(self.list_stack) - 1)
            indent = "  " * depth
            if self.list_stack:
                kind, counter = self.list_stack[-1]
                counter += 1
                self.list_stack[-1] = (kind, counter)
                marker = f"{counter}." if kind == "ol" else "-"
            else:
                marker = "-"
            self.emit(f"{indent}{marker} ")
            return
        if tag == "blockquote":
            self.block_break()
            self.blockquote_depth += 1
            return
        if tag in ("td", "th"):
            self.emit(" | ")
            return
        if tag == "tr":
            self.line_break()
            self.emit("|")
            return
        # transparent containers: div, section, article, figure, figcaption, span,
        # table, thead, tbody — fall through (no-op)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript", "head", "iframe", "form", "nav", "aside", "header", "footer"):
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_level = 0
            self.block_break()
            return
        if tag == "p":
            self.block_break()
            return
        if tag in ("strong", "b"):
            self.emit("**")
            return
        if tag in ("em", "i"):
            self.emit("*")
            return
        if tag == "code" and self.in_code:
            self.emit("`")
            self.in_code -= 1
            return
        if tag == "pre":
            self.in_pre = max(0, self.in_pre - 1)
            self.emit("\n```")
            self.block_break()
            return
        if tag == "a":
            href = self.in_a.pop() if self.in_a else ""
            self.emit(f"]({href})" if href else "]()")
            return
        if tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.block_break()
            return
        if tag == "li":
            self.line_break()
            return
        if tag == "blockquote":
            self.blockquote_depth = max(0, self.blockquote_depth - 1)
            self.block_break()
            return
        if tag == "tr":
            self.line_break()
            return

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return
        if not data:
            return
        if self.in_pre:
            self.parts.append(data)
            self.last_was_block_break = False
            return
        # collapse internal whitespace; keep meaningful spaces
        text = re.sub(r"\s+", " ", data)
        if text == " " and (self.last_was_block_break or self._last_char_is_break()):
            return
        # blockquote prefix on every fresh line
        if self.blockquote_depth > 0 and self._last_char_is_break():
            self.parts.append("> " * self.blockquote_depth)
            self.last_was_block_break = False
        self.emit(text)

    def _last_char_is_break(self) -> bool:
        if not self.parts:
            return True
        return self.parts[-1].endswith("\n")


def html_to_markdown(html: str) -> str:
    parser = _HtmlToMd()
    parser.feed(html or "")
    parser.close()
    md = "".join(parser.parts)
    # Tidy: collapse 3+ newlines to 2; trim trailing spaces per line
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"
