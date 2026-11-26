// Smooth Mode: the Shine (./Shine.tsx) looks at how smoothly this phone really draws while everything moves, and calms
// itself on a phone that cannot keep up, so the app always feels fast.
//   FULL  = everything moves (the look as designed).
//   CALM  = only the glass glint still crosses; the turning edge, the colour change and the stars rest.
//   STILL = nothing moves (the same look as under Reduce Motion). At this level the rest of the app follows too
//           (src/motion.tsx): endless decoration rests and celebrations take the calm form made for Reduce Motion.
// Frames are counted on the UI thread, where the Shine runs, and only while a Shine is moving at FULL. What the phone
// needed is kept on the phone, so a slow phone starts calm the next time. After a week it gets one more look at FULL:
// a phone that was only busy or hot that day gets its whole shine back.
import { useEffect, useSyncExternalStore } from "react";
import { runOnJS, useFrameCallback, useSharedValue } from "react-native-reanimated";
import { storage } from "@/src/utils/storage";

export const FULL = 0, CALM = 1, STILL = 2;
export type ShineLevel = typeof FULL | typeof CALM | typeof STILL;

const LOOK_MS = 2000; // one look = two seconds of frames
const WAIT_MS = 250; // a longer gap is the app waiting (in the background), not a slow frame
const SLOW_MS = 1000 / 48; // under 48 frames a second on average: this phone is not keeping up
const CRAWL_MS = 1000 / 30; // under 30: it cannot move anything smoothly
const LOOKS = 2; // slow looks in a row before anything changes
const SETTLE_MS = 1500; // a screen that has just opened is busy with its own loading: not looked at
const AGAIN_MS = 7 * 86400 * 1000;
const KEY = "shine.level.v1"; // kept as "level:time"

let level: ShineLevel = FULL, moving = 0, settle = 0, slow = 0, sum = 0;
const listeners = new Set<() => void>();
const subscribe = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
const tell = () => listeners.forEach(listener => listener());

/** The level to start with, from what an earlier look kept on this phone. */
export function startLevel(kept: unknown, now: number): ShineLevel {
  const [was, at] = typeof kept === "string" ? kept.split(":").map(Number) : [];
  return (was === CALM || was === STILL) && at <= now && now - at < AGAIN_MS ? was : FULL;
}
void storage.getItem<string>(KEY, "").then(kept => {
  const start = startLevel(kept, Date.now());
  if (start !== FULL && level === FULL) { level = start; tell(); }
});

/** A Shine that is not resting says so while it is on screen; the function it gets back takes that word back. */
export function shineMoves() {
  settle = Date.now() + SETTLE_MS; // new pieces: a screen or a row has just appeared
  if (++moving === 1) tell();
  return () => { if (--moving === 0) tell(); };
}

/** One look has ended: `average` = milliseconds per frame over it. Two slow looks in a row calm the Shine. */
export function looked(average: number, now = Date.now()) {
  if (level !== FULL || !moving || now - LOOK_MS < settle) return;
  if (!(average > SLOW_MS)) { slow = 0; sum = 0; return; }
  sum += average;
  if (++slow < LOOKS) return;
  level = sum / slow > CRAWL_MS ? STILL : CALM;
  slow = 0; sum = 0;
  void storage.setItem(KEY, `${level}:${now}`);
  tell();
}

export const useShineLevel = () => useSyncExternalStore(subscribe, () => level, () => FULL as ShineLevel);

/** Mounted once, at the root: counts the frames, and only while a Shine is moving at FULL. Draws nothing. */
export function SmoothMode() {
  const watching = useSyncExternalStore(subscribe, () => level === FULL && moving > 0, () => false);
  const frames = useSharedValue(0), time = useSharedValue(0);
  const counter = useFrameCallback(frame => {
    const gap = frame.timeSincePreviousFrame;
    if (gap == null || gap > WAIT_MS) return;
    frames.value += 1; time.value += gap;
    if (time.value < LOOK_MS) return;
    const average = time.value / frames.value;
    frames.value = 0; time.value = 0;
    runOnJS(looked)(average);
  }, false);
  useEffect(() => { frames.set(0); time.set(0); counter.setActive(watching); }, [watching, counter, frames, time]);
  return null;
}
