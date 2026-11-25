// Whether "Matched" (JEE Main questions that matched ours) is on: Home then shows the Matched card in place of the All
// India series card, and the sign-in screen offers it too. Our server decides (the `matched` switch of /api/app/switches,
// backend/matched.py): from the day after the All India series' last day, or when the owner switches it on or off. So the
// day can change without a new app build. The last answer is kept on the phone: the next launch has the right card from
// its first frame, also without a network.
import { useEffect, useSyncExternalStore } from "react";
import { AppState } from "react-native";
import { appSwitches, askSwitches, onAppSwitches } from "@/src/api/client";
import { ARENA } from "@/src/arenaMode";
import { storage } from "@/src/utils/storage";

const KEY = "matched.on", AGAIN = 30 * 60 * 1000;
let on = false, started = false, askedAt = 0;
const listeners = new Set<() => void>();
const set = (value: boolean) => { if (value !== on) { on = value; listeners.forEach(fn => fn()); } };
const ask = (again = false) => { askedAt = Date.now(); askSwitches(again); };

function start() {
  if (started || ARENA) return; // the browser arena is Rapid Fire only
  started = true;
  const answered = () => {
    const s = appSwitches();
    if (!s) return;
    set(s.matched === true);
    void storage.setItem(KEY, s.matched === true);
  };
  void storage.getItem<boolean>(KEY, false).then(kept => { if (!appSwitches()) set(kept === true); });
  onAppSwitches(answered);
  answered();
  ask();
  // An app left open over midnight asks again when the student comes back to it.
  AppState.addEventListener("change", state => { if (state === "active" && Date.now() - askedAt > AGAIN) ask(true); });
}

const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };
const read = () => on;
export function useMatchedOn() {
  useEffect(start, []);
  return useSyncExternalStore(subscribe, read, read);
}

/** Mounted once at the root, so the answer is in before Home or the sign-in screen is drawn. */
export function MatchedGate() {
  useMatchedOn();
  return null;
}
