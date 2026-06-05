#!/usr/bin/env python3
"""Browser-rendered page/article/tweet to Markdown.

This is intentionally dependency-free. The online path talks to browser-relay
and injects one of the adapter scripts in scripts/adapters/. The offline path is
used by verify.sh and by agents that already have an extracted JSON fixture.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from html2md import html_to_markdown


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTERS = SCRIPTS / "adapters"
DEFAULT_RELAY_URL = "http://127.0.0.1:18795"


class PageToMarkdownError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def choose_adapter(url: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    host = urllib.parse.urlparse(url).netloc.lower()
    if host in {"x.com", "twitter.com"} or host.endswith(".x.com") or host.endswith(".twitter.com"):
        return "x"
    if host == "mp.weixin.qq.com":
        return "wechat"
    return "generic"


def plan_url(url: str, adapter: str | None = None) -> dict[str, Any]:
    chosen = choose_adapter(url, adapter)
    parsed = urllib.parse.urlparse(url)
    kind = "page"
    if chosen == "x":
        if re.search(r"/(?:i/)?article/\d+", parsed.path):
            kind = "x_article"
        elif re.search(r"/status(?:es)?/\d+", parsed.path):
            kind = "tweet"
        else:
            kind = "x_unknown"
    elif chosen == "wechat":
        kind = "wechat_article"
    return {
        "url": url,
        "host": parsed.netloc,
        "adapter": chosen,
        "kind": kind,
        "adapterPath": str((ADAPTERS / f"{chosen}.js").relative_to(ROOT)),
    }


def sanitize_slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:120] or "untitled"


def yaml_quote(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None or value == "" or value == []:
            continue
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def first_photo(media: list[dict[str, Any]] | None) -> str | None:
    for item in media or []:
        if item.get("type") == "photo" and item.get("url"):
            return str(item["url"])
    return None


def media_to_markdown(media: list[dict[str, Any]] | None) -> str:
    parts: list[str] = []
    for item in media or []:
        typ = item.get("type")
        if typ == "photo" and item.get("url"):
            alt = str(item.get("alt") or "")
            parts.append(f"![{alt}]({item['url']})")
        elif typ in {"video", "gif"}:
            url = item.get("bestUrl") or item.get("posterUrl")
            if url:
                parts.append(f"[{typ}]({url})")
    return "\n".join(parts)


def render_thread(result: dict[str, Any], requested_url: str) -> tuple[str, dict[str, Any]]:
    thread = result.get("thread") or []
    author = result.get("author") or (thread[0].get("author") if thread else None) or {}
    handle = author.get("handle") or author.get("username")
    author_name = author.get("name") or handle
    root = next((t for t in thread if t.get("isRoot")), thread[0] if thread else {})
    root_url = root.get("url") or result.get("url") or requested_url
    root_media = root.get("media") or []

    body_parts: list[str] = []
    for idx, node in enumerate(thread, start=1):
        if len(thread) > 1:
            body_parts.append(f"## {idx}\n")
        text = node.get("htmlText") or node.get("text") or ""
        if text:
            body_parts.append(html_to_markdown(f"<p>{text}</p>").strip())
        media_md = media_to_markdown(node.get("media"))
        if media_md:
            body_parts.append(media_md)
        if node.get("url"):
            body_parts.append(f"[查看推文]({node['url']})")
        if node.get("quotedTweet"):
            quoted = node["quotedTweet"]
            q_author = quoted.get("author") or {}
            q_handle = q_author.get("handle") or q_author.get("name") or "quoted"
            q_text = quoted.get("text") or ""
            body_parts.append(f"> @{q_handle}: {q_text}")

    meta = {
        "url": root_url,
        "requestedUrl": requested_url,
        "author": f"{author_name} (@{handle})" if author_name and handle else author_name,
        "authorName": author_name,
        "authorUsername": handle,
        "tweetCount": len(thread),
        "coverImage": first_photo(root_media),
        "extractedVia": "browser-relay",
        "adapter": result.get("adapter") or "x",
        "extractedAt": now_iso(),
    }
    return frontmatter(meta) + "\n\n".join(p for p in body_parts if p).strip() + "\n", meta


def render_page(result: dict[str, Any], requested_url: str) -> tuple[str, dict[str, Any]]:
    article = result.get("article")
    body_html = result.get("bodyHtml") or (article or {}).get("html") or ""
    title = result.get("title") or (article or {}).get("title") or ""
    author = result.get("author") or {}
    author_name = author.get("name") if isinstance(author, dict) else None
    md_body = html_to_markdown(body_html)
    if title and not md_body.lstrip().startswith("#"):
        md_body = f"# {title}\n\n{md_body}"
    meta = {
        "url": result.get("url") or requested_url,
        "requestedUrl": requested_url,
        "title": title,
        "author": author_name,
        "publishedAt": result.get("publishedAt"),
        "coverImage": first_photo(result.get("media")),
        "extractedVia": "browser-relay",
        "adapter": result.get("adapter") or "generic",
        "extractedAt": now_iso(),
    }
    return frontmatter(meta) + md_body.strip() + "\n", meta


def build_markdown(result: dict[str, Any], requested_url: str) -> tuple[str, dict[str, Any]]:
    kind = result.get("kind")
    if kind == "tweet":
        return render_thread(result, requested_url)
    return render_page(result, requested_url)


def relay_request(relay_url: str, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    url = relay_url.rstrip("/") + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise PageToMarkdownError(f"browser-relay request failed: {exc}") from exc
    return json.loads(raw) if raw else None


def load_adapter_script(adapter: str) -> str:
    path = ADAPTERS / f"{adapter}.js"
    if not path.exists():
        raise PageToMarkdownError(f"unknown adapter: {adapter}")
    return path.read_text(encoding="utf-8")


def extract_with_relay(url: str, adapter: str, relay_url: str, tab_id: str | None = None) -> dict[str, Any]:
    debug = relay_request(relay_url, "GET", "/api/debug")
    if isinstance(debug, dict) and debug.get("connected") is False:
        raise PageToMarkdownError("Chrome extension not connected")
    body: dict[str, Any] = {"url": url}
    if tab_id:
        body["tabId"] = tab_id
    relay_request(relay_url, "POST", "/api/navigate", body)
    time.sleep(1.5)
    script = load_adapter_script(adapter)
    expression = f"(async () => {{ {script}; return await window.__isaliExtract(); }})()"
    eval_body: dict[str, Any] = {"expression": expression}
    if tab_id:
        eval_body["tabId"] = tab_id
    response = relay_request(relay_url, "POST", "/api/eval", eval_body)
    if isinstance(response, dict) and "result" in response:
        result = response["result"]
    else:
        result = response
    if isinstance(result, str):
        result = json.loads(result)
    if not isinstance(result, dict):
        raise PageToMarkdownError(f"unexpected relay result: {type(result).__name__}")
    return result


def default_output_path(result: dict[str, Any], requested_url: str) -> Path:
    meta_title = result.get("title") or ((result.get("article") or {}).get("title")) or requested_url
    adapter = result.get("adapter") or choose_adapter(requested_url)
    slug = sanitize_slug(meta_title)
    return Path("page-to-markdown") / adapter / f"{slug}.md"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a browser-rendered page to Markdown.")
    parser.add_argument("url", nargs="?", help="URL to extract")
    parser.add_argument("-o", "--output", help="Markdown output path")
    parser.add_argument("--adapter", choices=["generic", "wechat", "x"], help="Force adapter")
    parser.add_argument("--relay-url", default=DEFAULT_RELAY_URL, help="browser-relay base URL")
    parser.add_argument("--tab-id", help="Chrome tab id for browser-relay")
    parser.add_argument("--plan", action="store_true", help="Print extraction plan and exit")
    parser.add_argument("--json", action="store_true", help="Print extracted JSON instead of Markdown")
    parser.add_argument("--from-json", help="Render Markdown from an extracted JSON fixture")
    parser.add_argument("--health", action="store_true", help="Check browser-relay health")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.health:
        print(json.dumps(relay_request(args.relay_url, "GET", "/api/debug"), ensure_ascii=False, indent=2))
        return 0
    if not args.url and not args.from_json:
        raise PageToMarkdownError("url or --from-json is required")

    requested_url = args.url or "fixture://local"
    adapter = choose_adapter(requested_url, args.adapter)
    if args.plan:
        print(json.dumps(plan_url(requested_url, adapter), ensure_ascii=False, indent=2))
        return 0

    if args.from_json:
        result = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    else:
        result = extract_with_relay(requested_url, adapter, args.relay_url, args.tab_id)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    markdown, _meta = build_markdown(result, requested_url)
    if args.output:
        output = Path(args.output)
    else:
        output = default_output_path(result, requested_url)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PageToMarkdownError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
