import { api, apiRaw, getAssetAccount, getAssetEpoch, onAssetScopeReset, privateAssets, registerAssetManifest, RawResult } from "./client";

type Stage = { until: number; promise: Promise<any>; ctl: AbortController; timer?: ReturnType<typeof setTimeout> };
const attempts = new Map<string, Stage>(), results = new Map<string, Stage>();
onAssetScopeReset(() => { for (const map of [attempts, results]) { for (const e of map.values()) { e.ctl.abort(); clearTimeout(e.timer); } map.clear(); } });
const received = new WeakMap<object, number>();
const mono = () => globalThis.performance?.now?.() ?? Date.now();
export const receivedAt = (data: object) => received.get(data) ?? mono();
const cancelled = () => Object.assign(new Error("Account changed."), { name: "AbortError" });

export function prepareImages(data: any, solutions = false, version = "original") {
  if (!getAssetAccount() || !data?.id || !Array.isArray(data.questions)) return;
  const rows = data.questions.filter((q: any) => solutions || !q.bonus || !!data.bonus_unlocked_at);
  registerAssetManifest(data.id, rows, solutions, version, true);
  privateAssets.selectGroup(data.id);
  const paths = rows.flatMap((q: any) => (solutions ? ["question", "solution"] : ["question"]).flatMap(kind =>
    Array.from({ length: Number(kind === "question" ? q.asset_count : q.solution_asset_count) || 0 }, (_, i) =>
      `/attempts/${encodeURIComponent(data.id)}/questions/${encodeURIComponent(q.id)}/asset/${kind}/${i}${version === "original" ? "" : `?score_version=${encodeURIComponent(version)}`}`)));
  privateAssets.preload(paths);
}

function stage(map: Map<string, Stage>, key: string, load: (signal: AbortSignal) => Promise<any>) {
  const current = map.get(key);
  if (current && current.until > Date.now()) return current.promise;
  for (const [k, v] of map) if (v.until <= Date.now()) { clearTimeout(v.timer); v.ctl.abort(); map.delete(k); }
  const ctl = new AbortController(), until = Date.now() + 15000;
  const entry: Stage = { until, ctl, promise: load(ctl.signal) };
  map.set(key, entry);
  void entry.promise.catch(() => {});
  entry.timer = setTimeout(() => { if (map.get(key)?.until === until) map.delete(key); }, 15000);
  return entry.promise;
}
export function warmAttempt(id: string, initial?: any): Promise<any> {
  const owner = getAssetAccount(), epoch = getAssetEpoch();
  if (!owner) return Promise.resolve(null);
  return stage(attempts, `${epoch}|${owner}|${id}`, async signal => {
    const data = Array.isArray(initial?.questions) ? initial : await api(`/attempts/${encodeURIComponent(id)}`, { signal });
    if (getAssetAccount() !== owner || getAssetEpoch() !== epoch) throw cancelled();
    received.set(data, mono()); prepareImages(data); return data;
  });
}
export async function loadAttempt(id: string) {
  const key = `${getAssetEpoch()}|${getAssetAccount()}|${id}`, data = await warmAttempt(id);
  clearTimeout(attempts.get(key)?.timer); attempts.delete(key); return data;
}
export function warmResult(id: string, version = "original"): Promise<RawResult<any>> {
  const owner = getAssetAccount(), epoch = getAssetEpoch();
  if (!owner) return Promise.reject(cancelled());
  return stage(results, `${epoch}|${owner}|${id}|${version}`, async signal => {
    const response = await apiRaw(`/attempts/${encodeURIComponent(id)}/results?score_version=${encodeURIComponent(version)}`, { signal });
    if (getAssetAccount() !== owner || getAssetEpoch() !== epoch) throw cancelled();
    if (response.status === 200 && response.data?.summary && response.data.status !== "embargoed") prepareImages(response.data, true, version);
    return response;
  });
}
export async function loadResult(id: string, version = "original") {
  const key = `${getAssetEpoch()}|${getAssetAccount()}|${id}|${version}`, data = await warmResult(id, version);
  clearTimeout(results.get(key)?.timer); results.delete(key); return data;
}