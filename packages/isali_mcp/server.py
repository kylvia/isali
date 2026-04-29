"""isali MCP server — wraps isali CLI as structured MCP tools.

Claude Code can invoke these tools with typed parameters instead of
constructing Bash command strings. Returns structured JSON outputs.

Install (once):
    uv venv ~/.isali/venv --python 3.11
    uv pip install --python ~/.isali/venv/bin/python "mcp[cli]"

Register to Claude Code:
    claude mcp add isali ~/.isali/venv/bin/python \
        ~/isali/packages/isali_mcp/server.py --scope user

Then restart Claude Code — tools appear as `mcp__isali__isali_*`.
"""
import json
import subprocess
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

ISALI = str(Path.home() / 'isali' / 'bin' / 'isali')

mcp = FastMCP('isali')


def _run(args: list, parse_json: bool = False) -> dict:
    """Execute isali CLI and return structured result."""
    cmd = [ISALI] + args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'exit_code': -1, 'error': 'timeout (300s)',
                'command': ' '.join(cmd)}

    result = {
        'ok': proc.returncode == 0,
        'exit_code': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr,
        'command': ' '.join(cmd),
    }
    if parse_json and proc.returncode == 0 and proc.stdout.strip():
        try:
            result['parsed'] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return result


@mcp.tool()
def isali_doctor() -> dict:
    """Run isali environment self-check (Python / bun / wechat-api.ts / credentials / logs).

    Returns structured JSON with each check's pass/fail + harness info.
    No side effects. Safe to call any time to diagnose issues.
    """
    return _run(['doctor', '--json'], parse_json=True)


@mcp.tool()
def isali_push(md_path: str, theme: str = 'default', cover: str = '',
               account: str = '', title: str = '', summary: str = '',
               dry_run: bool = False, plan: bool = False) -> dict:
    """Push a markdown article to WeChat Official Account draft box.

    Uses the vendored public-account SDK (skills/isali-wechat-post/scripts/wechat-api.ts).

    Args:
        md_path: absolute path to .md file
        theme: theme name (default / grace / simple / modern)
        cover: path to cover image (optional; falls back to first image in md)
        account: account alias for multi-account setup (optional)
        title: override title from frontmatter (optional)
        summary: override digest / summary (<=128 chars, optional)
        dry_run: render but don't publish
        plan: print plan and exit without any action

    Returns result with exit_code, stdout, stderr. On success, stdout contains
    the draft media_id.
    """
    args = ['push', md_path, '--theme', theme]
    if cover:
        args += ['--cover', cover]
    if account:
        args += ['--account', account]
    if title:
        args += ['--title', title]
    if summary:
        args += ['--summary', summary]
    if dry_run:
        args.append('--dry-run')
    if plan:
        args.append('--plan')
    return _run(args)


@mcp.tool()
def isali_cover(title: str, subtitle: str = '',
                bullets: Optional[list[str]] = None,
                style: str = '', out: str = '',
                plan: bool = False) -> dict:
    """Generate a WeChat article cover via gpt-image-2.

    Args:
        title: main title, large text in center
        subtitle: optional secondary title
        bullets: list of short data points shown at bottom with • markers
        style: preset name (minimal-tech / editorial / poster) or empty for profile default
        out: output path (optional; defaults to cover-TIMESTAMP.png in cwd)
        plan: only show prompt / path, do not call API

    Returns parsed JSON with action/path/size_bytes/duration_sec.
    """
    args = ['cover', '--title', title]
    if subtitle:
        args += ['--subtitle', subtitle]
    for b in bullets or []:
        args += ['--bullets', b]
    if style:
        args += ['--style', style]
    if out:
        args += ['--out', out]
    if plan:
        args.append('--plan')
    args.append('--json')
    return _run(args, parse_json=True)


@mcp.tool()
def isali_fetch(url: str, as_json: bool = False) -> dict:
    """Fetch URL content and convert to markdown.

    Handles:
      - mp.weixin.qq.com (WeChat Official Account) — UA-spoofed
      - x.com / twitter.com — requires cookies (not yet supported here)
      - generic webpages — plain urllib

    Args:
        url: target URL
        as_json: if true, also return parsed metadata (title/author/date/body)

    Returns result dict. On WeChat, parsed.title / parsed.author / parsed.date /
    parsed.markdown are populated.
    """
    args = ['fetch', url]
    if as_json:
        args.append('--json')
    return _run(args, parse_json=as_json)


@mcp.tool()
def isali_fact_check(md_path: str, strict: bool = False) -> dict:
    """Run static fact-check linter on a markdown article.

    Scans for:
      - numeric claims (percentages, ranks, elo, durations)
      - weak-source markers ("Reddit 上", "据说", etc.)
      - superlatives ("最快", "首个", ...)
      - quoted passages without visible [link] source nearby

    Does NOT verify correctness — flags items for human (or Claude) review.

    Args:
        md_path: path to .md file
        strict: any finding = exit 1 (vs default: numeric+weak both required)

    Returns parsed JSON with findings by category.
    """
    args = ['fact-check', md_path, '--json']
    if strict:
        args.append('--strict')
    return _run(args, parse_json=True)


if __name__ == '__main__':
    mcp.run(transport='stdio')
