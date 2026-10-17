import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, post, put } from "../../lib/api";
const postpone = (state, error) => {
  state.current.failures = Math.min(6, state.current.failures + 1);
  state.current.after = Date.now() + Math.max(error?.retryAfterMs || 0, Math.min(30000, 1000 * 2 ** state.current.failures) + Math.random() * 1500);
};
export function useAttempt(id, user) {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(null);
  const [pending, setPending] = useState({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const [seconds, setSeconds] = useState(null);
  const [conflict, setConflict] = useState(false);
  const data = useRef(null),
    drafts = useRef({}),
    running = useRef(false),
    loading = useRef(false),
    retryState = useRef({ failures: 0, after: 0 }),
    deadlineRetry = useRef({ failures: 0, after: 0 }),
    anchor = useRef({ server: 0, mono: 0 }),
    timer = useRef(null),
    conflictRef = useRef(false);
  const storage = `tejas-draft-${user.id}-${id}`;
  const confidenceStorage = `tejas-confidence-${user.id}-${id}`;
  const [confidencePreferences,setConfidencePreferences]=useState({});
  useEffect(()=>{
    try { const value=JSON.parse(localStorage.getItem(confidenceStorage)||'{}');setConfidencePreferences(value&&typeof value==='object'&&!Array.isArray(value)?value:{}); }
    catch { setConfidencePreferences({}); }
  },[confidenceStorage]);
  const chooseConfidence=(qid,value)=>{
    if(data.current?.confidence_observations?.[qid] || String(drafts.current[qid]?.value||data.current?.answers?.[qid]?.value||'').trim())return;
    const next={...confidencePreferences,[qid]:value};setConfidencePreferences(next);
    try{localStorage.setItem(confidenceStorage,JSON.stringify(next));}catch{setError('Optional confidence could not be stored on this device. Answer saving is unchanged.');}
  };
  const syncClock = (server) => {
    anchor.current = { server: server * 1000, mono: performance.now() };
  };
  const persist = useCallback(() => {
    setPending({ ...drafts.current });
    try {
      const encoded = JSON.stringify(drafts.current);
      if (localStorage.getItem(storage) !== encoded) {
        localStorage.setItem(storage, encoded);
        localStorage.setItem(storage.replace('tejas-draft-', 'tejas-draft-meta-'), JSON.stringify({title:data.current?.title,updated_at:Date.now(),attempt_id:id}));
      }
    } catch {
      setError(
        "Browser storage is unavailable. Pending drafts cannot survive a refresh; stay connected.",
      );
    }
  }, [storage, id]);
  const openResult = useCallback(
    () =>
      navigate(
        "/results/" +
          id +
          (Object.keys(drafts.current).length ? "?late=true" : ""),
        { replace: true },
      ),
    [id, navigate],
  );
  const load = useCallback(async () => {
    if (loading.current || Date.now() < retryState.current.after) return;
    loading.current = true;
    try {
      const d = await api("/attempts/" + id);
      syncClock(d.server_now);
      data.current = d;
      setAttempt(d);
      let stored = {};
      try {
        stored = JSON.parse(localStorage.getItem(storage) || "{}");
        if (!stored || typeof stored !== 'object' || Array.isArray(stored) || Object.values(stored).some(v=>!v || typeof v.value !== 'string' || typeof v.request_id !== 'string' || !Number.isInteger(v.revision))) throw new Error('Invalid draft');
      } catch {
        conflictRef.current = true; setConflict(true);
        setError('The local draft could not be read safely and has been preserved. Open Saved drafts from your account menu to inspect or explicitly discard it; it has not been scored.');
        return;
      }
      for (const [qid, v] of Object.entries(stored)) {
        if (d.answers[qid]?.request_id === v.request_id) delete stored[qid];
      }
      drafts.current = stored;
      persist();
      setError("");
      retryState.current = { failures: 0, after: 0 };
      if (d.status === "completed") openResult();
    } catch (e) {
      postpone(retryState, e);
      setError(e.message);
    } finally {
      loading.current = false;
    }
  }, [id, storage, persist, openResult]);
  useEffect(() => {
    load();
  }, [load]);
  const flush = useCallback(async () => {
    if (
      running.current ||
      Date.now() < retryState.current.after ||
      !navigator.onLine ||
      !data.current ||
      conflictRef.current
    )
      return;
    running.current = true;
    setSaving(true);
    try {
      for (const qid of Object.keys(drafts.current)) {
        const draft = drafts.current[qid];
        if (!draft) continue;
        const q = data.current.questions.find((q) => q.id === qid);
        if (
          q?.type === "integer" &&
          draft.value.trim() &&
          !/^[+−-]?[0-9]{1,20}$/.test(draft.value.trim())
        ) {
          setError(
            "Enter an exact integer. Decimal values such as 3.0 and pasted letters are not accepted. Your draft has not been scored.",
          );
          continue;
        }
        try {
          const res = await put(`/attempts/${id}/answers/${qid}`, draft);
          retryState.current = { failures: 0, after: 0 };
          if (res.current_revision > res.accepted.revision) {
            conflictRef.current = true;
            setConflict(true);
            setError('This retry was already saved, but another device has a newer answer. Review the server version before continuing.');
            break;
          }
          data.current.answers[qid] = res.accepted;
          const normalized = res.accepted.normalized_value;
          const observation = data.current.confidence_observations?.[qid];
          if (!observation && normalized) {
            data.current.confidence_observations = {...data.current.confidence_observations, [qid]: {probability: res.accepted.confidence ?? null, response: normalized}};
          } else if (observation?.probability != null && observation.response !== normalized) {
            data.current.confidence_changed_questions = [...new Set([...(data.current.confidence_changed_questions || []), qid])];
          }
          data.current.visited = [
            ...new Set([...(data.current.visited || []), qid]),
          ];
          setAttempt({ ...data.current, answers: { ...data.current.answers } });
          syncClock(res.server_now);
          if (drafts.current[qid]?.request_id === draft.request_id)
            delete drafts.current[qid];
          else if (drafts.current[qid])
            drafts.current[qid].revision = res.accepted.revision + 1;
          persist();
          setError("");
        } catch (e) {
          postpone(retryState, e);
          setError(e.message);
          if (e.status === 409) {
            const latest = await api("/attempts/" + id).catch(() => null);
            if (!latest) break;
            if (latest.status === "completed") {
              openResult();
              return;
            }
            if (latest.answers[qid]?.request_id === draft.request_id) {
              data.current = latest;
              setAttempt(latest);
              if (drafts.current[qid]?.request_id === draft.request_id)
                delete drafts.current[qid];
              else if (drafts.current[qid])
                drafts.current[qid].revision = latest.answers[qid].revision + 1;
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
      setSaving(false);
    }
  }, [id, persist, openResult]);
  useEffect(() => {
    const recover = async () => {
      if (!navigator.onLine) return;
      if (!data.current) await load();
      await flush();
    };
    const on = () => {
      setOnline(true);
      recover();
    };
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    let stopped = false;
    let retry;
    const schedule = () => {
      retry = setTimeout(async () => {
        await recover();
        if (!stopped) schedule();
      }, 5000 + Math.random() * 2000);
    };
    schedule();
    return () => {
      stopped = true;
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
      clearTimeout(retry);
      clearTimeout(timer.current);
    };
  }, [flush, load]);
  useEffect(() => {
    if (!attempt?.deadline) return;
    let checking = false;
    const confirmDeadline = async () => {
      if (checking || !navigator.onLine || Date.now() < deadlineRetry.current.after) return;
      checking = true;
      deadlineRetry.current.after = Date.now() + 5000 + Math.random() * 1500;
      try {
        const latest = await api("/attempts/" + id);
        deadlineRetry.current.failures = 0;
        syncClock(latest.server_now);
        if (latest.status === "completed") openResult();
      } catch (e) {
        postpone(deadlineRetry, e);
        setError(e.message);
      } finally {
        checking = false;
      }
    };
    const tick = () => {
      const serverNow =
        anchor.current.server + performance.now() - anchor.current.mono;
      const left = Math.max(
        0,
        Math.ceil((attempt.deadline * 1000 - serverNow) / 1000),
      );
      setSeconds(left);
      if (left === 0) confirmDeadline();
    };
    tick();
    const interval = setInterval(tick, 1000);
    const visible = () => {
      if (document.visibilityState === "visible") confirmDeadline();
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [attempt?.deadline, id, openResult]);
  useEffect(() => {
    const warn = (e) => {
      if (Object.keys(drafts.current).length) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);
  const edit = (qid, change) => {
    if (seconds === 0 || conflictRef.current) return;
    const old = drafts.current[qid] ||
      data.current.answers[qid] || { value: "", marked: false };
    const probability=Object.prototype.hasOwnProperty.call(confidencePreferences,qid)?confidencePreferences[qid]:old.confidence;
    drafts.current[qid] = {
      ...(typeof probability==='number' && Number.isFinite(probability) && probability>=0 && probability<=1 ? {confidence:probability}:{}),
      value: old.value,
      marked: old.marked,
      ...change,
      revision: (data.current.answers[qid]?.revision || 0) + 1,
      request_id: crypto.randomUUID(),
    };
    persist();
    clearTimeout(timer.current);
    timer.current = setTimeout(flush, 350);
  };
  const visit = useCallback(
    async (qid) => {
      if (
        !data.current ||
        data.current.status !== "active" ||
        data.current.visited?.includes(qid)
      )
        return;
      try {
        const r = await post(`/attempts/${id}/visit`, { question_id: qid });
        data.current.visited = r.visited;
        setAttempt({ ...data.current });
      } catch (e) {
        if (e.status === 409) load();
      }
    },
    [id, load],
  );
  const discard = () => {
    drafts.current = {};
    persist();
    conflictRef.current = false;
    setConflict(false);
    setError("");
    load();
  };
  const submit = async () => {
    setError("");
    await flush();
    if (running.current || Object.keys(drafts.current).length)
      throw new Error(
        "Wait for pending responses to be acknowledged before submitting.",
      );
    const receipt = await post("/attempts/" + id + "/submit");
    localStorage.removeItem(storage);
    localStorage.removeItem(storage.replace('tejas-draft-', 'tejas-draft-meta-'));
    localStorage.removeItem(confidenceStorage);
    navigate("/results/" + receipt.id);
  };
  const enterBonus = async () => {
    setError("");
    await flush();
    if (running.current || Object.keys(drafts.current).length)
      throw new Error("Wait for pending responses to be acknowledged before entering the bonus section.");
    const r = await post("/attempts/" + id + "/bonus");
    data.current = { ...data.current, bonus_unlocked_at: r.bonus_unlocked_at };
    setAttempt(data.current);
  };
  return {
    attempt,
    pending,
    error,
    setError,
    saving,
    online,
    seconds,
    conflict,
    load,
    edit,
    confidencePreferences,
    chooseConfidence,
    visit,
    discard,
    submit,
    enterBonus,
  };
}
