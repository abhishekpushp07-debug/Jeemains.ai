// The 🎯 Dream button on a college card: pins the seat (with the marks it needs) or unpins it. Max 5 per exam.
import { useEffect, useState } from "react";
import { buzz } from "@/src/components/ui";
import { Dream, DreamExam, dreamsOf, EXAM_NAME, MAX_DREAMS, removeDream, toggleDream, useDreams } from "./store";

export type DreamToggle = { on: boolean; busy: boolean; msg: string | null; toggle: () => void };

export function useDreamToggle(id: string, exam: DreamExam, build: () => Promise<Dream>): DreamToggle {
  const s = useDreams();
  const on = s.dreams.some(d => d.id === id);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(null), 4500);
    return () => clearTimeout(t);
  }, [msg]);
  const toggle = async () => {
    if (busy) return;
    if (on) { removeDream(id); setMsg(null); return; }
    if (dreamsOf(s, exam).length >= MAX_DREAMS) { setMsg(`${EXAM_NAME[exam]} ke 5 dream college ho gaye. Rank tab ke Dream panel se ek hatao, phir ye jodo.`); buzz("error"); return; }
    setBusy(true);
    try {
      const d = await build();
      if (toggleDream(d) === "added") { setMsg(`🎯 Dream mein juda: ${d.need} marks chahiye. Har mock ke baad dekho kitne door.`); buzz("success"); }
    } catch (e: any) { setMsg(e?.message || "Dream nahi juda. Dobara try karo."); }
    finally { setBusy(false); }
  };
  return { on, busy, msg, toggle };
}
