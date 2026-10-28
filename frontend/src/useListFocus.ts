import { useCallback, useRef } from "react";
import { AppState } from "react-native";
import { useFocusEffect } from "expo-router";

/** Keep visible lists current without duplicating the hook's first request. */
export function useListFocus(revalidate: () => void) {
  const first = useRef(true);
  useFocusEffect(useCallback(() => {
    if (first.current) first.current = false;
    else revalidate();
    const listener = AppState.addEventListener("change", state => {
      if (state === "active") revalidate();
    });
    return () => listener.remove();
  }, [revalidate]));
}