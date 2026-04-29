"""Fetchers + HTML→Markdown conversion.

Stateless; can be imported by other skills (isali-wechat-post's
fact-check flow, for example).
"""
import datetime
import re
import urllib.request
from typing import Optional

UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)


def detect_source(url: str) -> str:
    if 'mp.weixin.qq.com' in url:
        return 'wechat'
    if 'x.com' in url or 'twitter.com' in url:
        return 'x'
    return 'web'


def fetch_url(url: str, extra_headers: Optional[dict] = None, timeout: int = 60) -> str:
    headers = {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        ct = resp.headers.get('Content-Type', '')
    charset = 'utf-8'
    m = re.search(r'charset=([\w-]+)', ct)
    if m:
        charset = m.group(1)
    return body.decode(charset, errors='replace')


def parse_wechat(html: str) -> dict:
    """Extract WeChat article metadata and body HTML."""
    title = ''
    for pat in [r"var msg_title = '([^']+)'", r'var msg_title = "([^"]+)"',
                r'<h1[^>]*id="activity-name"[^>]*>([^<]+)</h1>']:
        m = re.search(pat, html)
        if m:
            title = m.group(1).strip()
            break

    author = ''
    for pat in [r"var nickname = '([^']+)'", r'var nickname = "([^"]+)"']:
        m = re.search(pat, html)
        if m:
            author = m.group(1)
            break

    date = ''
    m = re.search(r'var ct = "(\d+)"', html)
    if m:
        date = datetime.datetime.fromtimestamp(int(m.group(1))).strftime('%Y-%m-%d %H:%M')

    body_html = ''
    m = re.search(
        r'<div class="rich_media_content[^"]*"[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script',
        html,
        re.S,
    )
    if m:
        body_html = m.group(1)

    return {'title': title, 'author': author, 'date': date, 'body_html': body_html}


def html_to_md(html: str) -> str:
    """Minimal HTML → Markdown. Not a full parser; optimized for article bodies."""
    s = html

    # images first (before tags stripped)
    s = re.sub(r'<img[^>]+data-src="([^"]+)"[^>]*>', r'\n![](\1)\n', s)
    s = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', r'\n![](\1)\n', s)

    # headings (inside out to avoid nested capture)
    for n in range(6, 0, -1):
        s = re.sub(
            fr'<h{n}[^>]*>(.+?)</h{n}>',
            lambda m, lvl=n: f'\n\n{"#" * lvl} {m.group(1).strip()}\n\n',
            s,
            flags=re.S,
        )

    # lists
    s = re.sub(r'<li[^>]*>(.+?)</li>', r'- \1\n', s, flags=re.S | re.I)
    s = re.sub(r'</?(ul|ol)[^>]*>', '\n', s, flags=re.I)

    # block separators
    s = re.sub(r'<(p|div|section|article|blockquote)[^>]*>', '\n', s, flags=re.I)
    s = re.sub(r'</(p|div|section|article|blockquote)>', '\n', s, flags=re.I)
    s = re.sub(r'<br\s*/?>', '\n', s)

    # inline formatting
    s = re.sub(r'<(b|strong)[^>]*>(.+?)</\1>', r'**\2**', s, flags=re.S | re.I)
    s = re.sub(r'<(i|em)[^>]*>(.+?)</\1>', r'*\2*', s, flags=re.S | re.I)
    s = re.sub(r'<code[^>]*>(.+?)</code>', r'`\1`', s, flags=re.S | re.I)

    # links
    s = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.+?)</a>', r'[\2](\1)', s, flags=re.S | re.I)

    # strip remaining tags
    s = re.sub(r'<[^>]+>', '', s)

    # decode common entities
    for ent, ch in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
                    ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'")]:
        s = s.replace(ent, ch)

    # collapse whitespace
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n[ \t]+', '\n', s)
    s = re.sub(r'\n\s*\n\s*\n+', '\n\n', s)
    return s.strip()


def fetch_and_convert(url: str, cookies: Optional[dict] = None) -> dict:
    """High-level: fetch URL + convert to markdown.

    Returns dict with at least: source, url, markdown.
    On error returns dict with 'error' key (not raised).
    """
    src = detect_source(url)
    headers = {}
    if cookies:
        headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in cookies.items())

    try:
        html = fetch_url(url, extra_headers=headers)
    except Exception as e:
        return {'source': src, 'url': url, 'error': f'fetch failed: {e}'}

    if src == 'wechat':
        meta = parse_wechat(html)
        if not meta['body_html']:
            return {'source': 'wechat', 'url': url,
                    'error': 'could not locate rich_media_content. Is page rendered or blocked?'}
        body_md = html_to_md(meta['body_html'])
        md = f'# {meta["title"]}\n\n'
        if meta['author'] or meta['date']:
            md += f'> {meta["author"]} · {meta["date"]}\n\n'
        md += f'{body_md}\n\n---\n\nsource: {url}'
        return {
            'source': 'wechat',
            'url': url,
            'title': meta['title'],
            'author': meta['author'],
            'date': meta['date'],
            'body': body_md,
            'markdown': md,
        }

    if src == 'x':
        return {
            'source': 'x',
            'url': url,
            'error': 'X/Twitter requires auth cookies (auth_token + ct0); not yet implemented. See references/x-auth.md',
        }

    # generic web
    body_md = html_to_md(html)
    return {
        'source': 'web',
        'url': url,
        'body': body_md,
        'markdown': f'# Fetched from {url}\n\n{body_md}',
    }
