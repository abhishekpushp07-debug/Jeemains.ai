"""Original instrumental + sound design; no sampled commercial music."""
from pathlib import Path
import wave
import numpy as np

ROOT = Path(__file__).parent
SR, DURATION = 48000, 45
RNG = np.random.default_rng(20261028)


def add(track, sound, at, gain=1.0, pan=0.0):
    start = max(0, int(at * SR))
    length = min(len(sound), len(track) - start)
    if length <= 0:
        return
    angle = (pan + 1) * np.pi / 4
    track[start:start + length, 0] += sound[:length] * gain * np.cos(angle)
    track[start:start + length, 1] += sound[:length] * gain * np.sin(angle)


def tone(freq, duration, kind="bell"):
    t = np.arange(int(duration * SR)) / SR
    if kind == "pad":
        wave_ = sum(np.sin(2 * np.pi * freq * (1 + detune) * t) for detune in [-.002, 0, .002]) / 3
        wave_ += .2 * np.sin(2 * np.pi * freq * 2 * t)
        env = np.minimum(t / .9, 1) * np.minimum((duration - t) / 1.0, 1)
    elif kind == "bass":
        wave_ = np.sin(2 * np.pi * freq * t) + .15 * np.sin(2 * np.pi * freq * 2 * t)
        env = np.minimum(t / .015, 1) * np.exp(-t * 6)
    else:
        wave_ = np.sin(2 * np.pi * freq * t) + .2 * np.sin(2 * np.pi * freq * 2.005 * t)
        env = np.minimum(t / .007, 1) * np.exp(-t * 3.6)
    return wave_ * env


def percussion(kind):
    duration = .45 if kind == "kick" else .2 if kind == "snare" else .075
    t = np.arange(int(duration * SR)) / SR
    noise = RNG.standard_normal(len(t))
    if kind == "kick":
        phase = 2 * np.pi * (47 * t + 6 * (1 - np.exp(-t * 28)))
        return np.sin(phase) * np.exp(-t * 12) + .05 * noise * np.exp(-t * 180)
    high = np.concatenate(([0], np.diff(noise))) / 2
    if kind == "snare":
        return (.4 * high + .3 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22)
    return high * np.exp(-t * 90)


def compose():
    track = np.zeros((SR * DURATION, 2), dtype=np.float64)
    chords = [[146.832, 174.614, 220], [116.541, 146.832, 174.614], [130.813, 174.614, 220], [130.813, 164.814, 195.998]]
    for bar in range(12):
        chord = chords[bar % 4]
        at = bar * 4 - .35
        for i, freq in enumerate(chord):
            add(track, tone(freq, 5.2, "pad"), at, .11, (i - 1) * .55)
        if bar < 10:
            for beat in range(8):
                pos = bar * 4 + beat * .5
                if pos >= 3:
                    add(track, tone(chord[0] / 2, .48, "bass"), pos + .018, .23)
    notes = [293.665, 349.228, 440, 523.251, 440, 349.228, 391.995, 349.228]
    for n in range(88):
        at = n * .5 + .25
        if 3 <= at < 27 or 34 <= at < 42:
            note = tone(notes[n % len(notes)], 1.3)
            gain = .055 * RNG.uniform(.72, 1.05)
            pan = .38 * np.sin(n * 1.7)
            add(track, note, at + RNG.uniform(-.008, .008), gain, pan)
            add(track, note, at + .375, gain * .32, -pan)
    for beat in range(90):
        at = beat * .5
        if 3 <= at < 42:
            soft = .45 if 27 <= at < 34 else 1
            if beat % 2 == 0:
                add(track, percussion("kick"), at, .48 * soft)
            else:
                add(track, percussion("snare"), at + RNG.uniform(-.006, .006), .30 * soft)
            for off in [0, .25]:
                add(track, percussion("hat"), at + off, .07 * soft * RNG.uniform(.6, 1), RNG.uniform(-.6, .6))
    for at in [0, 3, 7, 13, 17, 22, 27, 29, 34, 39]:
        add(track, percussion("kick"), at, .42)
        t = np.arange(int(.6 * SR)) / SR
        airy = RNG.standard_normal(len(t))
        airy = np.convolve(airy, np.ones(12) / 12, mode="same") * np.sin(np.pi * t / .6) ** 2
        add(track, airy, max(0, at - .45), .13, -.5)
        add(track, airy, max(0, at - .35), .09, .5)
    for freq in [523.251, 659.255, 783.991]:
        add(track, tone(freq, 1.5), 11.65, .055)
    for freq in [146.832, 174.614, 220, 293.665]:
        add(track, tone(freq, 5.8, "pad"), 39.0, .13)
    fade = np.clip((DURATION - np.arange(len(track)) / SR) / 1.7, 0, 1)
    track *= fade[:, None]
    peak = np.max(np.abs(track))
    track = np.tanh(track / max(peak, .01) * 1.1) * .90
    output = ROOT / "output/music-original.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SR)
        out.writeframes((track * 32767).astype("<i2").tobytes())
    print(f"Original stereo score: {DURATION}s, {SR}Hz")


if __name__ == "__main__":
    compose()