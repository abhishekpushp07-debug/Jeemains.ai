"""TEST-ONLY iter168: decode /tmp/iter168_png vs /tmp/iter166_png (if present): pixel-equality, size, mode, bytes."""
import os, numpy as np
from PIL import Image
A, B = '/tmp/iter166_png', '/tmp/iter168_png'
for f in sorted(os.listdir(B)):
    if not f.endswith('.png'):
        continue
    b = Image.open(os.path.join(B, f)); bb = np.asarray(b.convert('RGB'))
    line = f'{f}: {b.size} {b.mode} {os.path.getsize(os.path.join(B, f))}B'
    pa = os.path.join(A, f)
    if os.path.exists(pa):
        a = Image.open(pa); aa = np.asarray(a.convert('RGB'))
        line += f' | 166 {a.size} {a.mode} {os.path.getsize(pa)}B pixel_equal={aa.shape == bb.shape and bool((aa == bb).all())}'
    print(line)
