"""Offline: the 30-second "Dream Unlocked" cheer track: 128 BPM, 64 beats = 30 s, then the last chord rings out.
Synthesised here (no samples, no external service) and stored as AAC .m4a in backend/rf_art/sound/. The app downloads it
the first time a dream college is unlocked, so it never adds to the app size. Count k of the dance = beat k of this track
(SPINS must match LEAD_SPIN in frontend/src/dream/routine.ts). Run: python backend/rapidfire/make_dream_cheer.py"""
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR, BPM, BEATS, TAIL = 32000, 128, 64, 1.8
BEAT = 60 / BPM
N = int(SR * (BEATS * BEAT + TAIL))
OUT = Path(__file__).parent.parent / "rf_art" / "sound"
SPINS = [10, 14, 18, 22, 32, 34, 36, 45, 47, 50, 54, 61]
rng = np.random.default_rng(11)


def tt(d):
    return np.arange(int(SR * d)) / SR


def filt(x, kind, f, order=2):
    w = [v / (SR / 2) for v in f] if isinstance(f, (list, tuple)) else f / (SR / 2)
    b, a = butter(order, w, btype=kind)
    return lfilter(b, a, x)


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def place(buf, beat, sig, gain=1.0):
    i = int(round(beat * BEAT * SR))
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i] * gain


def fade(sig, a=0.004, r=0.03):
    n, ai, ri = len(sig), int(SR * a), int(SR * r)
    e = np.ones(n)
    e[:ai] = np.linspace(0, 1, ai)
    e[n - ri:] *= np.linspace(1, 0, ri)
    return sig * e


def saw(f, d, detune=0.0):
    ph = np.cumsum(np.full(int(SR * d), f * (1 + detune))) / SR
    return 2 * (ph % 1.0) - 1


# --- instruments ---------------------------------------------------------------------------------------------------
def kick(d=0.42):
    x = tt(d)
    f = 48 + 100 * np.exp(-x * 26)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * np.exp(-x * 7)
    click = np.sin(2 * np.pi * 1700 * x) * np.exp(-x * 320) * 0.5
    return body + click


def clap(d=0.26):
    x, n = tt(d), filt(noise(d), "band", [900, 3400])
    e = sum(np.where(x >= o, np.exp(-(x - o) * 190), 0) for o in (0, 0.011, 0.023)) + 0.55 * np.exp(-x * 17)
    return n * e


def hat(open_=False):
    d = 0.26 if open_ else 0.05
    return filt(noise(d), "high", 7000) * np.exp(-tt(d) * (13 if open_ else 75))


def snare(d=0.2):
    x = tt(d)
    return np.sin(2 * np.pi * 195 * x) * np.exp(-x * 32) * 0.6 + filt(noise(d), "band", [1500, 7000]) * np.exp(-x * 24)


def crash(d=2.2):
    x = tt(d)
    return (filt(noise(d), "high", 3800) + 0.4 * filt(noise(d), "band", [6000, 11000])) * np.exp(-x * 2.0)


def bass(f, d=0.2):
    s = saw(f, d) + 0.6 * saw(f, d, 0.006)
    return fade(filt(s, "low", 950) * np.exp(-tt(d) * 5), 0.004, 0.04)


def stab(chord, d=0.2, cut=2600):
    s = sum(saw(f, d) + saw(f, d, 0.005) for f in chord)
    return fade(filt(s, "low", cut) * np.exp(-tt(d) * 8), 0.003, 0.04)


def pad(chord, d, cut=1500):
    s = sum(saw(f, d, k) for f in chord for k in (-0.004, 0, 0.0045))
    e = np.minimum(1, tt(d) / 0.35) * np.minimum(1, (d - tt(d)) / 0.5)
    return filt(s, "low", cut) * e


def lead(semi, d):
    """A bright brass section: three detuned saws, the filter opening on each note (a fanfare "blat"), light vibrato."""
    x = tt(d)
    f = 523.25 * 2 ** (semi / 12) * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * x) * np.minimum(1, x / 0.25))
    s = sum(2 * ((np.cumsum(f * (1 + k)) / SR) % 1.0) - 1 for k in (-0.004, 0, 0.005))
    dark, bright = filt(s, "low", 1100), filt(s, "low", 3600)
    s = dark + (bright - dark) * np.exp(-x * 7)
    return fade(s * (0.75 + 0.25 * np.exp(-x * 5)), 0.012, 0.05)


def riser(d, lo=300, hi=6000):
    n, out, k = noise(d), np.zeros(int(SR * d)), 28
    seg = len(out) // k
    for i in range(k):
        c = lo * (hi / lo) ** (i / (k - 1))
        out[i * seg:(i + 1) * seg] = filt(n, "band", [c * 0.7, min(c * 1.4, SR / 2 - 100)])[i * seg:(i + 1) * seg]
    x = tt(d)
    tone = np.sin(2 * np.pi * np.cumsum(220 * 4 ** (x / d)) / SR) * 0.25
    return (out + tone) * (x / d) ** 2


def whoosh(d=0.42):
    x = tt(d)
    return riser(d, 600, 5000) * np.sin(np.pi * x / d) ** 2 * 2.2


def crowd(d):
    x, s = tt(d), np.zeros(int(SR * d))
    for lo, hi in ((350, 1100), (700, 2200), (1400, 3800)):
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(2, 6) * x + rng.uniform(0, 6))
        s += filt(noise(d), "band", [lo, hi]) * lfo
    for _ in range(7):  # "woo!" voices gliding up
        st, ln = rng.uniform(0, d * 0.5), rng.uniform(0.5, 1.1)
        y = tt(ln)
        f0 = rng.uniform(520, 760)
        v = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.45 * np.minimum(1, y / 0.25)) * (1 + 0.012 * np.sin(2 * np.pi * 6 * y))) / SR)
        v *= np.sin(np.pi * y / ln) * 0.18
        i = int(st * SR)
        s[i:i + len(v)] += v[: len(s) - i]
    return s * np.minimum(1, x / 0.35) * np.minimum(1, (d - x) / (d * 0.6))


def chime(notes, d=1.6):
    x, s = tt(d), np.zeros(int(SR * d))
    for i, f in enumerate(notes):
        st = int(i * 0.07 * SR)
        y = x[: len(x) - st]
        s[st:] += np.sin(2 * np.pi * f * y) * np.exp(-y * 3.5)
    return s


# --- arrangement: 8 sections of 8 counts (intro, verse, verse, build, drop with spins, verse, verse, finale) -------------
C, G, AM, F = (261.63, 329.63, 392.0), (196.0, 246.94, 293.66), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63)
CHORDS, ROOTS = [C, G, AM, F], [130.81, 98.0, 110.0, 87.31]
# A cheer fanfare: "ta-ta-TAAA, ta-da-da" and its answer. None = the note before keeps ringing.
HOOK_A = [-5, -5, 0, None, 4, None, 2, 0, 2, None, 4, 2, 0, None, None, None]
HOOK_B = [7, 7, 9, None, 7, None, 4, 2, 4, None, 7, 4, 2, None, 0, None]
drums, music, melody, fx = np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N)
kicks = []
for b in range(BEATS):
    sec, bar, q = b // 8, b // 4, b % 4
    ch, root = CHORDS[bar % 4], ROOTS[bar % 4]
    groove = sec in (1, 2, 4, 5, 6)
    if groove or (sec == 0 and b >= 4) or (sec == 3 and b < 28):
        place(drums, b, kick(), 1.0 if sec else 0.55 + 0.1 * (b - 4)); kicks.append(b)
    if sec == 3 and b >= 28:
        for k in (0, 0.5):
            place(drums, b + k, kick(), 0.6 + 0.08 * (b - 28)); kicks.append(b + k)
    if (groove or sec == 0 or (sec == 3 and b < 28)) and q in (1, 3):
        place(drums, b, clap(), 0.55)
    if groove or (sec == 0 and b >= 2):
        place(drums, b + 0.5, hat(open_=sec >= 4 and q == 3), 0.13 if sec >= 4 and q == 3 else 0.17)
        if sec >= 4:
            place(drums, b + 0.25, hat(), 0.07); place(drums, b + 0.75, hat(), 0.07)
    if groove:
        place(music, b + 0.5, bass(root), 0.55)
        if q in (0, 2):
            place(music, b + 0.5, stab(ch), 0.16)
        if sec == 4:
            place(music, b + 0.75, stab([f * 2 for f in ch], 0.16, 4200), 0.1)
    if sec in (1, 2, 4, 5, 6):  # the hook: 16 eighth notes over 2 bars (octave up on the drop)
        hook, up = (HOOK_A if sec in (1, 4, 5) else HOOK_B), (12 if sec == 4 else 0)
        for k in (0, 1):
            i = (b % 8) * 2 + k
            if hook[i] is not None:
                ring = 1 + next((j for j, v in enumerate(hook[i + 1:]) if v is not None), len(hook) - i - 1)
                place(melody, b + k * 0.5, lead(hook[i] + up, BEAT * 0.5 * ring * 0.92), 0.3 if up else 0.4)
    if sec == 3:  # the build: chord tones climbing in 16ths
        for k in range(4):
            f = ch[(k + b) % 3] * 2 ** ((b - 24) // 3)
            place(melody, b + k * 0.25, stab([f], 0.12, 5000), 0.1 + 0.02 * (b - 24))
    if sec == 0 and q == 0:
        place(music, b, pad(ch, BEAT * 4), 0.09 + 0.04 * bar)
    if sec == 3:
        if q == 0:
            place(music, b, pad(ch, BEAT * 4, 1200 + 600 * (bar - 6)), 0.1)
        if b >= 28:
            for k in ((0, 0.5) if b < 30 else (0, 0.25, 0.5, 0.75)):
                place(drums, b + k, snare(), 0.25 + 0.07 * (b - 28) + 0.1 * k)
    if sec == 7 and b < 60:
        for k in (0, 0.25, 0.5, 0.75):
            place(drums, b + k, snare(), 0.22 + 0.08 * (b - 56) + 0.06 * k)
for b in SPINS:
    place(fx, b, whoosh(), 0.28)
place(fx, 24, riser(8 * BEAT - 0.1), 0.3)
place(fx, 56, riser(4 * BEAT - 0.05, 400, 7000), 0.34)
for b, g in ((8, 0.22), (32, 0.32), (40, 0.2), (48, 0.2), (60, 0.38)):
    place(drums, b, crash(), g)
place(fx, 0, crowd(3.2), 0.5)
place(fx, 31.5, crowd(1.6), 0.18)
place(fx, 60, crowd(4 * BEAT + TAIL), 0.55)
# Finale: one big hit on count 60 that rings to the end, sparkles on top.
place(drums, 60, kick(0.6), 1.1); kicks.append(60)
place(drums, 60, clap(), 0.6)
place(music, 60, pad([f * 2 for f in C] + list(C), 4 * BEAT + TAIL, 2600), 0.16)
place(music, 60, stab([f * 2 for f in C], 0.5, 4200), 0.22)
place(music, 60, bass(130.81, 4 * BEAT + TAIL - 0.2) * 1.0, 0.45)
place(fx, 60, chime((1046.5, 1318.5, 1568.0, 2093.0, 2637.0), 2.4), 0.2)
place(fx, 62, chime((1568.0, 2093.0, 2637.0, 3136.0), 2.0), 0.14)

gap = slice(int(31.5 * BEAT * SR), int(32 * BEAT * SR))
for bus in (drums, music, melody):
    bus[gap] *= np.linspace(1, 0, gap.stop - gap.start) ** 3
boom = tt(1.2)
place(drums, 32, np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-boom * 9)) / SR) * np.exp(-boom * 2.8), 0.9)

# Sidechain: the music ducks under each kick, the "pump" of a dance track.
x = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    t0 = k * BEAT
    m = x >= t0
    duck[m] = np.minimum(duck[m], 1 - 0.55 * np.exp(-(x[m] - t0) * 11))
echo = np.zeros(N)
d3 = int(SR * BEAT * 0.75)
for k, g in ((1, 0.32), (2, 0.14)):
    echo[d3 * k:] += melody[: N - d3 * k] * g
ir = noise(0.9) * np.exp(-tt(0.9) * 6)
room = fftconvolve(filt(melody + music * 0.5, "low", 5000), filt(ir, "low", 4000))[:N]
room *= 0.25 / (np.max(np.abs(room)) + 1e-9)
mix = drums * 0.85 + music * duck + (melody + echo) * (0.55 + 0.45 * duck) + room + fx * 0.8
mix = filt(mix, "low", 8200)
mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.15) * 0.95
mix *= np.minimum(1, (N - np.arange(N)) / (SR * 0.6))  # last 0.6 s fade

OUT.mkdir(parents=True, exist_ok=True)
wav, m4a = OUT / "dream_cheer.wav", OUT / "dream_cheer.m4a"
with wave.open(str(wav), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "80k", "-movflags", "+faststart", str(m4a)], check=True)
wav.unlink()
print(m4a, round(N / SR, 2), "s", m4a.stat().st_size // 1024, "KB")
