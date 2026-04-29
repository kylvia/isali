"""Just-in-time profile loader.

Loads ~/.isali/profile.yaml (or $ISALI_PROFILE) lazily.
Cached after first access. Supports dot-notation: get('content.tone').

Prefers PyYAML (full spec). Falls back to a built-in minimal parser
that supports nested dicts + flat lists (enough for our profile format).
"""
from pathlib import Path
import os

PROFILE_PATH = Path(os.environ.get('ISALI_PROFILE') or (Path.home() / '.isali' / 'profile.yaml'))
_DEFAULT = Path(__file__).resolve().parent.parent.parent / 'profiles' / 'default.yaml'

_cache = None


def _cast(s):
    """Cast scalar string to int/float/bool/None."""
    if not isinstance(s, str):
        return s
    low = s.lower()
    if low in ('true', 'yes', 'on'):
        return True
    if low in ('false', 'no', 'off'):
        return False
    if low in ('null', 'none', '~', ''):
        return None
    # try int
    try:
        if '.' not in s and 'e' not in low:
            return int(s)
    except ValueError:
        pass
    # try float
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _strip_inline_comment(line: str) -> str:
    """Remove ' # ...' comments while respecting simple quotes."""
    in_q, qc = False, None
    for i, ch in enumerate(line):
        if ch in ('"', "'"):
            if not in_q:
                in_q, qc = True, ch
            elif qc == ch:
                in_q = False
        elif ch == '#' and not in_q and i > 0 and line[i - 1] == ' ':
            return line[:i].rstrip()
    return line


def _parse_yaml_fallback(text: str) -> dict:
    """Minimal YAML reader — supports nested dicts + flat lists + scalars.

    Does NOT support: multi-line block scalars (|, >), anchors/aliases,
    flow style, list-of-dict. For complex profiles, use PyYAML.
    """
    lines_filtered = []
    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.lstrip()
        if not s or s.startswith('#') or s in ('---', '...'):
            continue
        lines_filtered.append(_strip_inline_comment(line))

    result = {}
    stack = [(-1, result, None)]  # (indent, container, last_key_of_parent)
    for line in lines_filtered:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            stack = [(-1, result, None)]
        parent_indent, parent, parent_key = stack[-1]

        # list item
        if stripped.startswith('- '):
            val = stripped[2:].strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            casted = _cast(val)
            if isinstance(parent, dict) and parent_key is not None:
                if not isinstance(parent.get(parent_key), list):
                    parent[parent_key] = []
                parent[parent_key].append(casted)
            continue

        if ':' not in stripped:
            continue
        key, _, val = stripped.partition(':')
        key = key.strip()
        val = val.strip()

        if val:
            # inline scalar
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            parent[key] = _cast(val)
        else:
            # nested block — container TBD by next line
            parent[key] = {}
            stack.append((indent, parent[key], key))
    return result


def _parse_yaml(text: str) -> dict:
    try:
        import yaml  # PyYAML, full spec
        return yaml.safe_load(text) or {}
    except ImportError:
        return _parse_yaml_fallback(text)


def load(force: bool = False) -> dict:
    global _cache
    if _cache is not None and not force:
        return _cache
    path = PROFILE_PATH if PROFILE_PATH.exists() else _DEFAULT
    _cache = _parse_yaml(path.read_text()) if path.exists() else {}
    return _cache


def get(path: str, default=None):
    """Dot-notation: get('content.tone')."""
    d = load()
    for key in path.split('.'):
        if not isinstance(d, dict) or key not in d:
            return default
        d = d[key]
    return d


def path_info() -> str:
    which = PROFILE_PATH if PROFILE_PATH.exists() else _DEFAULT
    kind = 'user' if which == PROFILE_PATH else 'default template'
    return f'{which} ({kind})'


def which() -> Path:
    """Return path of the currently active profile file."""
    return PROFILE_PATH if PROFILE_PATH.exists() else _DEFAULT
