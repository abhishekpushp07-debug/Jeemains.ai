import { useCallback, useEffect, useRef, useState } from "react";
import { AppState } from "react-native";
import { api, ApiError, post, put, uuid } from "@/src/api/client";
import { Draft, DraftMap, loadDrafts, saveDrafts } from "@/src/drafts";
import { loadAttempt, receivedAt, warmResult, prepareImages } from "@/src/api/paperOpening";

export type Attempt = any;
const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());

function postpone(s: { failures: number; after: number }, e?: any) {
  s.failures = Math.min(6, s.failures + 1);
  s.after = Date.now() + Math.max(e?.retryAfterMs || 0, Math.min(30000, 1000 * 2 ** s.failures) + Math.random() * 1500);
}

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
  const loading = useRef(false);
  const retryState = useRef({ failures: 0, after: 0 });
  const anchor = useRef({ server: 0, mono: 0 });
  const debounce = useRef<any>(null);
  const conflictRef = useRef(false);
  const done = useRef(onCompleted);
  useEffect(() => { done.current = onCompleted; }, [onCompleted]);

  const syncClock = (server: number, at = mono()) => (anchor.current = { server: server * 1000, mono: at });
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
      postpone(retryState.current, e);
      setError(e.message);
    } finally {
      loading.current = false;
    }
  }, [id, uid, persist]);

  const flush = useCallback(async () => {
    if (running.current || Date.now() < retryState.current.after || !data.current || conflictRef.current) return;
    running.current = true;
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
          postpone(retryState.current, e);
          setError(e.message);
          if (e.status === 409) {
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
      setInflight(null);
    }
  }, [id, persist]);

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
  useEffect(() => {
    if (!attempt?.deadline) return;
    let checking = false;
    const confirm = async () => {
      if (checking) return;
      checking = true;
      try {
        const latest = await api("/attempts/" + id);
        syncClock(latest.server_now);
        if (latest.status === "completed") done.current();
      } catch (e: any) {
        net(e);
      } finally {
        setTimeout(() => (checking = false), 5000);
      }
    };
    const tick = () => {
      const serverNow = anchor.current.server + mono() - anchor.current.mono;
      const left = Math.max(0, Math.ceil((attempt.deadline * 1000 - serverNow) / 1000));
      setSeconds(left);
      if (left === 0) confirm();
    };
    tick();
    const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }, [attempt?.deadline, id]);

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
    retryState.current.after = 0;
    await flush();
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
