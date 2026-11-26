import React, { createContext, useCallback, useContext, useState } from "react";
import { useFocusEffect } from "expo-router";
import { useReducedMotion } from "react-native-reanimated";
import { STILL, useShineLevel } from "@/src/analysis/smooth";

// Endless decoration (glitter rings, floating art, twinkles, clocks that tick every second) belongs to the screen the
// student is looking at. A screen covered by another one (the lobby under a match, Home under a test) stays mounted, so
// without this its animations and timers kept running behind the match and took frames away from it.
const InFront = createContext(true);

/** Put around a screen: everything inside learns whether that screen is the one in front. */
export function ScreenMotion({ children }: { children: React.ReactNode }) {
  const [front, setFront] = useState(true);
  useFocusEffect(useCallback(() => {
    setFront(true);
    return () => setFront(false);
  }, []));
  return <InFront.Provider value={front}>{children}</InFront.Provider>;
}

/** Put around a part of a screen that stays mounted while it is hidden (a pane of a tab): its endless motion rests while `on` is false. */
export function MotionWhile({ on, children }: { on: boolean; children: React.ReactNode }) {
  const front = useContext(InFront);
  return <InFront.Provider value={front && on}>{children}</InFront.Provider>;
}

/** False while this screen is covered by another screen. */
export const useScreenInFront = () => useContext(InFront);

/** True when a celebration or a pop-in takes its calm form (the one made for Reduce Motion): Reduce Motion is on, or
 *  this phone cannot move anything smoothly (Smooth Mode's lowest level, src/analysis/smooth.ts). */
export function useLowMotion() {
  const reduced = useReducedMotion();
  const level = useShineLevel();
  return !!reduced || level === STILL;
}

/** True when endless motion must rest: the screen is covered, Reduce Motion is on, or this phone cannot keep up. */
export function useStill() {
  const low = useLowMotion();
  return !useContext(InFront) || low;
}
