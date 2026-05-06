"""Core cover generation logic — usable as module or CLI.

Decoupled from argparse so it can be imported by other skills/scripts.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

from isali_core import logger, profile

try:
    import httpx as _httpx
except ImportError:
    _httpx = None

ROOT = Path(__file__).resolve().parent.parent
PRESETS_DIR = ROOT / 'presets'

DEFAULT_API_URL = 'https://ai.liaobots1.work/v1/chat/completions'
DEFAULT_MODEL = 'gpt-image-2'


def load_preset(name: str) -> str:
    """Load a prompt preset template by name (without .txt)."""
    path = PRESETS_DIR / f'{name}.txt'
    if not path.exists():
        available = sorted(p.stem for p in PRESETS_DIR.glob('*.txt'))
        raise FileNotFoundError(
            f'preset "{name}" not found. available: {available}'
        )
    return path.read_text()


def build_prompt(
    title: str,
    subtitle: str = '',
    bullets: list = None,
    style: str = None,
    aspect_ratio: str = None,
    brand_color: str = None,
) -> str:
    """Fill preset template with user values + profile defaults."""
    style = style or profile.get('cover.style_preset', 'minimal-tech')
    aspect_ratio = aspect_ratio or profile.get('cover.aspect_ratio', '2.35:1')
    brand_color = brand_color or profile.get('cover.brand_color', '#8087EA')
    bullets = bullets or []

    template = load_preset(style)
    bullets_str = '、'.join(f'"• {b}"' for b in bullets) if bullets else '不要底部数据条'

    return template.format(
        title=title,
        subtitle=subtitle,
        bullets_str=bullets_str,
        style=style,
        aspect_ratio=aspect_ratio,
        brand_color=brand_color,
    )


def generate_image(prompt: str, out_path: Path, timeout: int = 180) -> dict:
    """Call gpt-image-2 API, save PNG, return metadata dict."""
    api_url = os.environ.get('ISALI_IMAGE_API_URL') or profile.get(
        'image.api_url', DEFAULT_API_URL
    )
    api_key = os.environ.get('ISALI_IMAGE_API_KEY') or profile.get('image.api_key')
    if not api_key:
        sys.exit(
            'error: image API key not configured. Set env ISALI_IMAGE_API_KEY '
            'or add `image.api_key: "<key>"` to ~/.isali/profile.yaml'
        )
    model = os.environ.get('ISALI_IMAGE_MODEL') or profile.get('image.model', DEFAULT_MODEL)

    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 1,
        'stream': False,
    }

    # httpx > urllib for this gateway: urllib hits "Remote end closed connection
    # without response" against ai.liaobots1.work in ~3s, httpx works. Even
    # then, the gateway frequently disconnects the FIRST connection ~3s after
    # POST and accepts retries cleanly, so we retry up to 3 times.
    t0 = time.time()
    if _httpx is not None:
        last_exc = None
        data = None
        for attempt in range(3):
            try:
                with _httpx.Client(timeout=timeout) as c:
                    resp = c.post(api_url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                break
            except _httpx.RemoteProtocolError as e:
                last_exc = e
                continue
        if data is None:
            raise RuntimeError(f'all 3 attempts failed: {last_exc}')
    else:
        req = urllib.request.Request(
            api_url, method='POST', headers=headers,
            data=json.dumps(body).encode(),
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    dt = time.time() - t0

    content = data['choices'][0]['message']['content']

    # Two known response formats:
    #   1. base64 data URI inline:  data:image/png;base64,<...>
    #   2. markdown URL link:       ![image](https://.../foo.png)
    m_b64 = re.search(r'data:image/(\w+);base64,([A-Za-z0-9+/=]+)', content)
    m_url = re.search(r'!\[[^\]]*\]\((https?://[^\s)]+)\)', content)

    if m_b64:
        ext, b64 = m_b64.group(1), m_b64.group(2)
        img = base64.b64decode(b64)
    elif m_url:
        url = m_url.group(1)
        ext = url.rsplit('.', 1)[-1].split('?', 1)[0].lower()
        if ext not in ('png', 'jpg', 'jpeg', 'webp'):
            ext = 'png'
        # Same gateway flakiness applies to the image CDN: urllib often does an
        # IncompleteRead, httpx is more reliable. Retry a couple times.
        img = None
        last_exc = None
        for attempt in range(3):
            try:
                if _httpx is not None:
                    with _httpx.Client(timeout=timeout) as c:
                        r = c.get(url)
                        r.raise_for_status()
                        img = r.content
                else:
                    with urllib.request.urlopen(url, timeout=timeout) as r:
                        img = r.read()
                if img:
                    break
            except Exception as e:
                last_exc = e
                continue
        if not img:
            raise RuntimeError(f'image download failed after 3 attempts: {last_exc}')
    else:
        raise RuntimeError(f'no image in response. Head: {content[:200]}')

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img)

    return {
        'path': str(out_path),
        'size_bytes': len(img),
        'ext': ext,
        'duration_sec': round(dt, 2),
        'model': data.get('model', model),
    }


def generate(
    title: str,
    out_path: str,
    subtitle: str = '',
    bullets: list = None,
    style: str = None,
    prompt: str = None,
    plan: bool = False,
    dry_run: bool = False,
) -> dict:
    """High-level entry — compose prompt and optionally call API."""
    final_prompt = prompt or build_prompt(
        title=title, subtitle=subtitle, bullets=bullets or [], style=style
    )

    meta = {'prompt': final_prompt, 'out': out_path, 'style': style}

    if plan:
        return {'action': 'plan', **meta}
    if dry_run:
        return {'action': 'dry-run', 'prompt_length': len(final_prompt), **meta}

    result = generate_image(final_prompt, Path(out_path))
    logger.audit('cover_gen', title=title, style=style, **result)
    return {'action': 'generated', **result}
