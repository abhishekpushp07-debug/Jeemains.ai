"""Lossless PNG shrinking (oxipng): the same pixels in fewer bytes.

oxipng keeps Python's lock while it works, so it never runs inside the server: each group of pictures goes to a short-lived
process of its own. Every result is opened and compared pixel by pixel with its original; anything that differs, fails or
takes too long keeps the original bytes, so a picture can never come out worse or missing.
"""
import io, os, struct, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

LEVEL = 2
GROUP_SECONDS = 300


def _pack(items):
    return b''.join(struct.pack('>I', len(x)) + x for x in items)


def _unpack(raw):
    out, at = [], 0
    while at < len(raw):
        (n,) = struct.unpack_from('>I', raw, at)
        at += 4
        out.append(raw[at:at + n])
        at += n
        if at > len(raw):
            raise ValueError('cut short')
    return out


def _lanes():
    try:
        quota, period = open('/sys/fs/cgroup/cpu.max').read().split()
        if quota != 'max':
            return max(1, int(quota) // int(period))
    except (OSError, ValueError):
        pass
    return max(1, len(os.sched_getaffinity(0)))


def _group(items):
    try:
        done = subprocess.run([sys.executable, __file__], input=_pack(items), capture_output=True, timeout=GROUP_SECONDS, close_fds=True,
                              env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'})
        small = _unpack(done.stdout) if done.returncode == 0 else []
    except (OSError, subprocess.SubprocessError, struct.error, ValueError):
        small = []
    if len(small) != len(items):
        return list(items)
    return [s if s and len(s) < len(raw) else raw for s, raw in zip(small, items)]


def shrink_many(items):
    """Each PNG made smaller without changing a pixel; the list comes back in the same order."""
    items = list(items)
    if not items:
        return []
    lanes = min(8, _lanes(), len(items))
    groups = [items[i::lanes] for i in range(lanes)]
    with ThreadPoolExecutor(max_workers=lanes) as pool:
        done = list(pool.map(_group, groups))
    out = [None] * len(items)
    for lane, group in enumerate(done):
        out[lane::lanes] = group
    return out


def _same_pixels(a, b):
    from PIL import Image
    x, y = Image.open(io.BytesIO(a)), Image.open(io.BytesIO(b))
    return x.size == y.size and x.convert('RGBA').tobytes() == y.convert('RGBA').tobytes()


def _main():
    import oxipng
    out = []
    for raw in _unpack(sys.stdin.buffer.read()):
        try:
            small = oxipng.optimize_from_memory(raw, level=LEVEL, strip=oxipng.StripChunks.safe())
            out.append(small if len(small) < len(raw) and _same_pixels(raw, small) else b'')
        except Exception:  # noqa: BLE001  any trouble with one picture keeps its original
            out.append(b'')
    sys.stdout.buffer.write(_pack(out))


if __name__ == '__main__':
    _main()
