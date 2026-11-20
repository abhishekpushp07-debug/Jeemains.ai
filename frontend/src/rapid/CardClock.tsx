import React, { useEffect, useRef, useState } from "react";
import { Ring } from "@/src/components/Ring";
import { playSfx } from "@/src/sfx";

const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());

/**
 * The countdown ring of one card. It keeps its own seconds, so a tick redraws only the ring and never the whole card
 * (a full redraw every second made taps and swipes stutter on slower phones). Mount it with `key` = the card, so a new
 * card starts a fresh ring. `startedAt` is the screen's own clock for the card (read at every tick, never copied).
 * `onExpire` is called when the time is up; return `false` to be asked again 100 ms later (a retry that must wait).
 */
export function CardClock({ startedAt, limit, initial, running, expired, color, onExpire }: {
  startedAt: React.RefObject<number>; limit: number; initial?: number; running: boolean; expired?: boolean; color: string; onExpire: () => boolean | void;
}) {
  const [left, setLeft] = useState(() => Math.min(limit, initial ?? limit));
  const expire = useRef(onExpire), lastTick = useRef(0);
  expire.current = onExpire;
  useEffect(() => {
    if (!running) return;
    const iv = setInterval(() => {
      const l = limit - (mono() - startedAt.current);
      // Checked every 100 ms; the ring only redraws when the shown second changes.
      setLeft((prev) => (Math.ceil(prev / 1000) === Math.ceil(Math.max(0, l) / 1000) ? prev : Math.max(0, l)));
      const sec = Math.ceil(l / 1000);
      if (l > 0 && sec <= 5 && sec !== lastTick.current) { lastTick.current = sec; playSfx("tick", 0.6); }
      if (l <= 0 && expire.current() !== false) clearInterval(iv);
    }, 100);
    return () => clearInterval(iv);
  }, [running, limit, startedAt]);
  return <Ring light left={expired ? 0 : left} color={color} limit={limit} />;
}
