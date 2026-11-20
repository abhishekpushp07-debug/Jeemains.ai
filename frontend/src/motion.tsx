import React, { createContext, useCallback, useContext, useState } from "react";
import { useFocusEffect } from "expo-router";
import { useReducedMotion } from "react-native-reanimated";

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

/** False while this screen is covered by another screen. */
export const useScreenInFront = () => useContext(InFront);

/** True when endless motion must rest: Reduce Motion is on, or the screen is covered. */
export function useStill() {
  const reduced = useReducedMotion();
  return !useContext(InFront) || !!reduced;
}
