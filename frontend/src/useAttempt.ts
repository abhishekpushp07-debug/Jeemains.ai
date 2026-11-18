import { useCallback, useEffect, useRef, useState } from "react";
import { AppState } from "react-native";
import { api, ApiError, post, put, uuid } from "@/src/api/client";
import { Draft, DraftMap, loadDrafts, saveDrafts } from "@/src/drafts";
import { loadAttempt, receivedAt, warmResult, prepareImages } from "@/src/api/paperOpening";

export type Attempt = any;
const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());

function postpone(s: { failures: number; after: number }, e?: any, left?: number | null) {
  s.failures = Math.min(6, s.failures + 1);
  // In the last minute a failed save is retried within ~1.5 s: a 30 s pause there would miss the deadline.
  const cap = left != null && left < 60 ? 1500 : 30000;
  s.after = Date.now() + Math.min(Math.max(e?.retryAfterMs || 0, Math.min(cap, 1000 * 2 ** s.failures)), left != null && left < 60 ? 2000 : Infinity) + Math.random() * (cap < 30000 ? 500 : 1500);
}
const transient = (e: any) => !(e instanceof ApiError) || e.status === 0 || e.status === 408 || e.status === 429 || e.status >= 500;

// Native port of the web useAttempt contract: acknowledged autosave, immutable request IDs,
// revision conflicts surfaced (never auto-bumped), monotonic server-anchored timer.
export function useAttempt(id: string, uid: string, onCompleted: () => void) {
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [pending, setPending] = useState<DraftMap>({});
  const [inflight, setInflight] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(true);
  const [seconds, setSeconds] = useState<number | null>(null);
  const [conflict, setConflict] = useState(false);
  const data = useRef<Attempt | null>(null);
  const drafts = useRef<DraftMap>({});
  const running = useRef(false);
  const flight = useRef<Promise<void> | null>(null); // the save run on its way, if any
  const saveOffline = useRef(false); // the last save failed for network/busy reasons (not refused by the server)
  const loading = useRef(false);
  const retryState = useRef({ failures: 0, after: 0 });
  const anchor = useRef({ server: 0, mono: 0 });
  const debounce = useRef<any>(null);
  const conflictRef = useRef(false);
  const done = useRef(onCompleted);
  useEffect(() => { done.current = onCompleted; }, [onCompleted]);

  const syncClock = (server: number, at = mono()) => (anchor.current = { server: server * 1000, mono: at });
  const secondsLeft = () => data.current?.deadline ? (data.current.deadline * 1000 - (anchor.current.server + mono() - anchor.current.mono)) / 1000 : null;
  const persist = useCallback(() => {
    setPending({ ...drafts.current });
    saveDrafts(uid, id, data.current?.title || "Attempt", drafts.current);
  }, [uid, id]);
  const net = (e: any) => setOnline(!(e instanceof ApiError && e.status === 0));

  const load = useCallback(async () => {
    if (loading.current || Date.now() < retryState.current.after) return;
    loading.current = true;
    try {
      const d = await loadAttempt(id);
      if (!d) throw new Error("Sign in to open this attempt.");
      syncClock(d.server_now, receivedAt(d));
      data.current = d;
      setAttempt(d);
      setOnline(true);
      const stored = await loadDrafts(uid, id);
      if (stored === "corrupt") {
        conflictRef.current = true;
        setConflict(true);
        setError("The local draft could not be read safely and was preserved. It has not been scored.");
        return;
      }
      for (const [qid, v] of Object.entries(stored)) if (d.answers?.[qid]?.request_id === v.request_id) delete stored[qid];
      drafts.current = stored;
      persist();
      setError("");
      retryState.current = { failures: 0, after: 0 };
      if (d.status === "completed") done.current();
    } catch (e: any) {
      net(e);
      postpone(retryState.current, e, secondsLeft());
      setError(e.message);
    } finally {
      loading.current = false;
    }
  }, [id, uid, persist]);

  const flush = useCallback(async () => {
    if (running.current || Date.now() < retryState.current.after || !data.current || conflictRef.current) return;
    running.current = true;
    let finished = () => {};
    flight.current = new Promise<void>(resolve => { finished = resolve; });
    try {
      for (const qid of Object.keys(drafts.current)) {
        const draft = drafts.current[qid];
        if (!draft) continue;
        const q = data.current.questions.find((x: any) => x.id === qid);
        if (q?.type === "integer" && draft.value.trim() && !/^[+−-]?[0-9]{1,20}$/.test(draft.value.trim())) {
          setError("Enter an exact integer. Decimals and letters are not accepted. Your draft has not been scored.");
          continue;
        }
        setInflight(qid);
        try {
          const res = await put(`/attempts/${id}/answers/${qid}`, draft);
          setOnline(true);
          saveOffline.current = false;
          retryState.current = { failures: 0, after: 0 };
          if (res.current_revision > res.accepted.revision) {
            conflictRef.current = true;
            setConflict(true);
            setError("Another device saved a newer answer. Review the server version before continuing.");
            break;
          }
          data.current.answers = { ...data.current.answers, [qid]: res.accepted };
          data.current.visited = [...new Set([...(data.current.visited || []), qid])];
          setAttempt({ ...data.current });
          syncClock(res.server_now);
          // Only clear the draft if this ACK matches the exact pending command.
          if (drafts.current[qid]?.request_id === draft.request_id) delete drafts.current[qid];
          else if (drafts.current[qid]) drafts.current[qid].revision = res.accepted.revision + 1;
          persist();
          setError("");
        } catch (e: any) {
          net(e);
          saveOffline.current = transient(e);
          postpone(retryState.current, e, secondsLeft());
          setError(e.message);
          if (e.status === 409) {
            const left = secondsLeft();
            if (left != null && left <= 0) break; // time is up: the paper is sealed, the submit step takes over (no full re-download)
            const latest = await api("/attempts/" + id).catch(() => null);
            if (!latest) break;
            if (latest.status === "completed") {
              done.current();
              return;
            }
            if (latest.answers?.[qid]?.request_id === draft.request_id) {
              data.current = latest;
              setAttempt(latest);
              if (drafts.current[qid]?.request_id === draft.request_id) delete drafts.current[qid];
              else if (drafts.current[qid]) drafts.current[qid].revision = latest.answers[qid].revision + 1;
              persist();
            } else {
              conflictRef.current = true;
              setConflict(true);
            }
          }
          break;
        }
      }
    } finally {
      running.current = false;
      flight.current = null;
      finished();
      setInflight(null);
    }
  }, [id, persist]);

  // Before a submit: waits for a save run already on its way (it may have started before the last answers), then
  // sends whatever is still pending, ignoring the retry pause.
  const drain = useCallback(async () => {
    clearTimeout(debounce.current);
    if (flight.current) await flight.current;
    retryState.current.after = 0;
    await flush();
  }, [flush]);

  useEffect(() => {
    let alive = true;
    Promise.resolve().then(() => { if (alive) void load(); });
    return () => { alive = false; };
  }, [load]);

  useEffect(() => {
    let stopped = false;
    let t: any;
    const recover = async () => {
      if (!data.current) await load();
      await flush();
    };
    const loop = () => {
      t = setTimeout(async () => {
        await recover();
        if (!stopped) loop();
      }, 5000 + Math.random() * 2000);
    };
    loop();
    const sub = AppState.addEventListener("change", (s) => {
      if (s === "active") {
        retryState.current.after = 0;
        load().then(flush);
      }
    });
    return () => {
      stopped = true;
      clearTimeout(t);
      clearTimeout(debounce.current);
      sub.remove();
    };
  }, [flush, load]);

  // Timer: deadline − anchored server time (monotonic), never the device wall clock.
  // At 00:00 the paper is sealed. Each phone waits a random 0-10 s (a crowd must not reach the server in the same
  // second), sends its pending answers (also again before each retry: answers that failed offline get another go),
  // then submits. Answers still unsent because of the network hold the submit back for up to 3 retries (~40 s), then
  // it goes anyway. Busy or offline: retried with growing, spread pauses that honour Retry-After. Never a full paper
  // re-download every 5 s.
  useEffect(() => {
    if (!attempt?.deadline) return;
    let sealing = false, stopped = false, timer: any;
    const seal = async (round: number) => {
      if (stopped) return;
      try {
        await drain();
        if (round < 3 && saveOffline.current && Object.keys(drafts.current).length)
          throw new ApiError("Kuch answers abhi save nahi hue. Internet check karo, hum dobara bhej rahe hain.", 0);
        await post(`/attempts/${id}/submit`, {});
        void warmResult(id).catch(() => {});
        await saveDrafts(uid, id, "", {});
        if (!stopped) done.current();
      } catch (e: any) {
        net(e);
        if (stopped) return;
        if (!transient(e)) {
          // Refused (for example already sealed by the server): one look tells whether the paper is completed.
          const latest = await api("/attempts/" + id).catch(() => null);
          if (latest?.status === "completed") { await saveDrafts(uid, id, "", {}); if (!stopped) done.current(); }
          else setError(e.message);
          return;
        }
        const wait = Math.max(e?.retryAfterMs || 0, Math.min(30000, 5000 * 2 ** round)) + Math.random() * 5000;
        timer = setTimeout(() => seal(round + 1), wait);
      }
    };
    const tick = () => {
      const serverNow = anchor.current.server + mono() - anchor.current.mono;
      const left = Math.max(0, Math.ceil((attempt.deadline * 1000 - serverNow) / 1000));
      setSeconds(left);
      if (left === 0 && !sealing) { sealing = true; timer = setTimeout(() => seal(0), Math.random() * 10000); }
    };
    tick();
    const iv = setInterval(tick, 1000);
    return () => { stopped = true; clearInterval(iv); clearTimeout(timer); };
  }, [attempt?.deadline, id, uid, drain]);

  const edit = (qid: string, change: Partial<Draft>) => {
    if (seconds === 0 || conflictRef.current || !data.current) return;
    const old: any = drafts.current[qid] || data.current.answers?.[qid] || { value: "", marked: false };
    const next: Draft = {
      value: old.value ?? "",
      marked: !!old.marked,
      ...(typeof old.confidence === "number" ? { confidence: old.confidence } : {}),
      ...change,
      revision: (data.current.answers?.[qid]?.revision || 0) + 1,
      request_id: uuid(),
    };
    drafts.current[qid] = next;
    persist();
    clearTimeout(debounce.current);
    debounce.current = setTimeout(flush, 350);
  };

  const visit = useCallback(async (qid: string) => {
    const d = data.current;
    if (!d || d.status !== "active" || d.visited?.includes(qid)) return;
    try {
      const r = await post(`/attempts/${id}/visit`, { question_id: qid });
      if (Array.isArray(r?.visited)) {
        d.visited = r.visited;
        setAttempt({ ...d });
      }
    } catch (e: any) {
      if (e.status === 409) load();
    }
  }, [id, load]);

  const discard = () => {
    drafts.current = {};
    persist();
    conflictRef.current = false;
    setConflict(false);
    setError("");
    retryState.current.after = 0;
    load();
  };

  const settle = async () => {
    await drain();
    if (running.current || Object.keys(drafts.current).length) throw new Error("Wait until every answer shows Saved. Pending answers are not submitted.");
  };

  const submit = async () => {
    setError("");
    await settle();
    const receipt = await post(`/attempts/${id}/submit`, {});
    // Grading/embargo rules stay authoritative. Warm only a released result.
    void warmResult(id).catch(() => {});
    await saveDrafts(uid, id, "", {});
    return receipt;
  };

  const enterBonus = async () => {
    setError("");
    await settle();
    const r = await post(`/attempts/${id}/bonus`, {});
    data.current = { ...data.current, bonus_unlocked_at: r.bonus_unlocked_at };
    prepareImages(data.current);
    setAttempt(data.current);
  };

  return { attempt, pending, inflight, error, setError, online, seconds, conflict, load, edit, visit, discard, submit, enterBonus };
}
