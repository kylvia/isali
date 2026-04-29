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

ROOT = Path(__file__).resolve().parent.parent
PRESETS_DIR = ROOT / 'presets'

DEFAULT_API_URL = 'https://ai.liaobots.work/v1/chat/completions'
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

    req = urllib.request.Request(
        api_url,
        method='POST',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        data=json.dumps(
            {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 1,
                'stream': False,
            }
        ).encode(),
    )

    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    dt = time.time() - t0

    content = data['choices'][0]['message']['content']
    m = re.search(r'data:image/(\w+);base64,([A-Za-z0-9+/=]+)', content)
    if not m:
        raise RuntimeError(f'no image in response. Head: {content[:200]}')

    ext, b64 = m.group(1), m.group(2)
    img = base64.b64decode(b64)
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
