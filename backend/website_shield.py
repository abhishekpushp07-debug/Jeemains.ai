"""Shield in front of the website (jeelive.ai), one per server process (Phase 3, Level 7).

When the website stops answering (connection errors, time-outs, its 502/503/504/52x pages, or answers slower than SLOW
seconds) for at least MIN_FAILS of the calls of the last WINDOW seconds, and for at least half of them, the shield
opens: for a few seconds no call is sent at all and the caller gets an immediate "website busy" answer (the app keeps the
student's work safe and tries again). Then ONE call is let through as a probe: if it works, everything flows again; if
not, the shield stays shut twice as long (at most OPEN_MAX seconds). So a website outage costs the website nothing more,
and it costs this server nothing either: no pile of requests left hanging for 28 seconds each, and Rapid Fire, which
runs on this server, keeps playing."""
import time
from collections import deque

import aiohttp

WINDOW, MIN_FAILS, FAIL_SHARE = 10.0, 8, 0.5
OPEN_FIRST, OPEN_MAX = 5.0, 30.0
SLOW = 10.0  # seconds: an answer slower than this counts as a failure (a website this slow is down for a student)
DOWN_STATUS = {502, 503, 504, 520, 521, 522, 523, 524, 525, 526, 527, 530}
BOUNDS = (50, 100, 200, 500, 1000, 2000, 5000, 10000)  # ms buckets for the website's speed (App Health)


class WebsiteDown(aiohttp.ClientError):
    """Raised instead of calling the website while the shield is shut. An aiohttp.ClientError, so every existing
    `except UpstreamError` already treats it as "the website did not answer"."""
    def __init__(self, retry_after: float):
        super().__init__("website shield open")
        self.retry_after = max(1, int(retry_after + 0.999))


class Shield:
    def __init__(self):
        self.calls: deque = deque()  # (time, ok) of the last WINDOW seconds
        self.fails = 0
        self.state = "closed"  # closed -> open -> half (one probe) -> closed | open
        self.open_until = 0.0
        self.open_for = OPEN_FIRST
        self.probing = False
        self.opened = 0  # how many times it opened since this process started
        self.last_trouble = 0.0  # wall clock of the last failed call
        self.minutes: dict = {}  # minute -> [calls, failed, refused, hist...]

    def _minute(self):
        m = int(time.time() // 60)
        row = self.minutes.get(m)
        if row is None:
            row = self.minutes[m] = [0, 0, 0] + [0] * (len(BOUNDS) + 1)
            for old in [k for k in self.minutes if k < m - 6]:
                del self.minutes[old]
        return row

    def allow(self) -> bool:
        """Before a call: True if this call is the probe, False for an ordinary call; raises WebsiteDown while shut."""
        now = time.monotonic()
        if self.state == "open":
            if now < self.open_until:
                self._minute()[2] += 1
                raise WebsiteDown(self.open_until - now)
            self.state = "half"
        if self.state == "half":
            if self.probing:
                self._minute()[2] += 1
                raise WebsiteDown(1)
            self.probing = True
            return True
        return False

    def _open(self, now):
        self.state, self.open_until = "open", now + self.open_for
        self.opened += 1
        self.calls.clear()
        self.fails = 0

    def record(self, ok, probe: bool, seconds: float):
        """After a call: ok True/False, or None when the caller went away (a cancelled call says nothing about the website)."""
        now = time.monotonic()
        if probe:
            self.probing = False
        if ok is None:
            return
        row = self._minute()
        row[0] += 1
        ms = seconds * 1000
        row[3 + next((i for i, b in enumerate(BOUNDS) if ms <= b), len(BOUNDS))] += 1
        if not ok:
            row[1] += 1
            self.last_trouble = time.time()
        if probe:
            if ok:
                self.state, self.open_for = "closed", OPEN_FIRST
            else:
                self.open_for = min(OPEN_MAX, self.open_for * 2)
                self._open(now)
            return
        self.calls.append((now, ok))
        self.fails += not ok
        while self.calls and self.calls[0][0] < now - WINDOW:
            self.fails -= not self.calls.popleft()[1]
        if self.state == "closed" and self.fails >= MIN_FAILS and self.fails >= FAIL_SHARE * len(self.calls):
            self._open(now)

    def snapshot(self) -> dict:
        now = int(time.time() // 60)
        rows = [r for m, r in self.minutes.items() if m > now - 5]
        total = [sum(col) for col in zip(*rows)] if rows else [0] * (3 + len(BOUNDS) + 1)
        state = self.state
        if state == "open" and time.monotonic() >= self.open_until:
            state = "half"
        return {"state": state, "opened": self.opened, "last_trouble_ts": self.last_trouble or None,
                "calls": total[0], "failed": total[1], "refused": total[2], "hist": total[3:]}


shield = Shield()
