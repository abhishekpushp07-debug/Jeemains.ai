import { useSyncExternalStore } from "react";
import { storage } from "@/src/utils/storage";
import { PIECE_ZOOM } from "./pieces";

// The text size a student picks for cut questions stays on the phone (the website keeps it in the browser the same way):
// picked once, every cut question - in a test and in its solutions - opens at that size.
const KEY = "piece.zoom.v1";
let step = 0, picked = false;
const listeners = new Set<() => void>();
const valid = (n: unknown) => Math.max(0, Math.min(PIECE_ZOOM.length - 1, Math.round(Number(n)) || 0));
const tell = () => listeners.forEach(f => f());

void storage.getItem<number>(KEY, 0).then(saved => {
  // A size picked while the saved one was still being read wins.
  if (!picked && valid(saved) !== step) { step = valid(saved); tell(); }
});

export function setPieceZoom(next: number) {
  picked = true;
  if (valid(next) === step) return;
  step = valid(next);
  tell();
  void storage.setItem(KEY, step);
}
const read = () => step;
/** Which step of PIECE_ZOOM is in use, on every screen that shows a cut question. */
export const usePieceZoom = () => useSyncExternalStore(f => { listeners.add(f); return () => { listeners.delete(f); }; }, read, read);
