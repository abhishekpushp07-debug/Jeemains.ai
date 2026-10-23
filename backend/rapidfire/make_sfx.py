"""Offline: synthesise short entry sound effects (WAV, 22 kHz mono) into frontend/assets/sfx/. No external service."""
import wave
from pathlib import Path
import numpy as np

SR = 22050
OUT = Path(__file__).parent.parent.parent / "frontend" / "assets" / "sfx"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)


def t(d):
    return np.linspace(0, d, int(SR * d), endpoint=False)


def env(n, a=0.02, r=0.4):
    x = np.ones(n)
    ai, ri = int(SR * a), int(SR * r)
    x[:ai] = np.linspace(0, 1, ai)
    x[-ri:] *= np.linspace(1, 0, ri) ** 2
    return x


def lp(x, k):  # cheap low-pass (moving average)
    return np.convolve(x, np.ones(k) / k, mode="same")


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def whoosh(d=1.0, lo=40, hi=4):
    n = noise(d)
    out = np.zeros_like(n)
    seg = len(n) // 20
    for i in range(20):  # filter opens then closes -> swoosh
        k = int(lo + (hi - lo) * np.sin(np.pi * i / 19))
        out[i * seg:(i + 1) * seg] = lp(n, max(1, k))[i * seg:(i + 1) * seg]
    return out * env(len(n), 0.25, 0.5)


def boom(d=1.2, f0=120, f1=35):
    x = t(d)
    f = f0 * (f1 / f0) ** (x / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (s + 0.4 * lp(noise(d), 30)) * np.exp(-x * 3.2)


def chime(d=1.2, notes=(1318, 1568, 1976, 2637)):
    x = t(d)
    s = np.zeros_like(x)
    for i, f in enumerate(notes):
        st = int(i * 0.08 * SR)
        y = x[: len(x) - st]
        s[st:] += np.sin(2 * np.pi * f * y) * np.exp(-y * 4)
    return s


def thunder(d=1.6):
    n = noise(d)
    crack = n * np.exp(-t(d) * 18)
    rumble = lp(n, 60) * 6 * np.exp(-t(d) * 1.8)
    return crack + rumble


def engine(d=1.0):
    x = t(d)
    f = 70 + 260 * (x / d) ** 1.5
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return (lp(saw, 4) + 0.3 * whoosh(d, 20, 2)) * env(len(x), 0.05, 0.3)


def fire(d=1.3):
    n = lp(noise(d), 8)
    crackle = (rng.random(len(n)) > 0.997) * rng.uniform(-1, 1, len(n))
    return (n * 0.7 + lp(crackle, 3) * 8) * env(len(n), 0.1, 0.5) + 0.6 * boom(d, 90, 40)


def cosmic(d=1.6):
    x = t(d)
    s = sum(np.sin(2 * np.pi * f * x + np.sin(2 * np.pi * 0.7 * x) * 3) for f in (220, 330, 440, 660)) / 4
    return s * env(len(x), 0.3, 0.8) + 0.3 * chime(d)


def rise(d=1.2):
    x = t(d)
    f = 200 * (8 ** (x / d))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.05, 0.2) * 0.6 + whoosh(d) * 0.5


SFX = {
    "entry_rocket": lambda: rise() + boom(0.0 + 1.2) * 0.6,
    "entry_lightning": thunder,
    "entry_supercar": engine,
    "entry_crown": lambda: chime(1.4) + 0.4 * boom(1.4, 200, 80),
    "entry_dragon": fire,
    "entry_blackhole": lambda: np.concatenate([whoosh(0.8, 2, 60)[::-1], boom(0.8, 60, 25)]),
    "entry_meteor": lambda: np.concatenate([whoosh(0.6), boom(1.0, 90, 25)]),
    "entry_galaxy": cosmic,
    "entry_phoenix": lambda: fire(1.3) * 0.6 + chime(1.3, (880, 1175, 1760)) * 0.6,
    "entry_tornado": lambda: whoosh(1.5, 30, 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 6 * t(1.5))),
    "vs": lambda: boom(0.9, 160, 40) + 0.5 * noise(0.9) * np.exp(-t(0.9) * 25),
    "go": lambda: chime(0.6, (988, 1319)),
    "correct": lambda: chime(0.45, (1047, 1568)),
    "wrong": lambda: (np.sign(np.sin(2 * np.pi * 150 * t(0.35))) * 0.4 + np.sin(2 * np.pi * 110 * t(0.35))) * np.exp(-t(0.35) * 7),
    "combo": lambda: chime(0.7, (1047, 1319, 1568, 2093, 2637)),
    "tick": lambda: np.sin(2 * np.pi * 1800 * t(0.05)) * np.exp(-t(0.05) * 90),
    "win": lambda: chime(1.6, (523, 659, 784, 1047, 1319, 1568)) + 0.4 * boom(1.6, 200, 90),
    "lose": lambda: sum(np.sin(2 * np.pi * f * t(1.0)) for f in (392, 370, 349)) * np.exp(-t(1.0) * 2.2),
    "levelup": lambda: np.concatenate([rise(0.6) * 0.5, chime(1.0, (1047, 1319, 1568, 2093))]),
    "coin": lambda: chime(0.5, (1976, 2637)),
}

for name, fn in SFX.items():
    s = fn()
    s = s / (np.max(np.abs(s)) + 1e-9) * 0.85
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((s * 32767).astype(np.int16).tobytes())
    print(name, len(s) / SR)
