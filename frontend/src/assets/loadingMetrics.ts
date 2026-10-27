type Stage = "disk_read" | "image_network" | "image_encode" | "image_paint" | "math_update";
const samples = new Map<Stage, number[]>();
const counts = new Map<string, number>();
export const clock = () => globalThis.performance?.now?.() ?? Date.now();
/** Device-local bounded aggregate timings only. No URLs, IDs, text or credentials. */
export const loadingMetrics = {
  record(stage: Stage, ms: number) { if (!Number.isFinite(ms) || ms < 0) return; const values = samples.get(stage) || []; values.push(ms); if (values.length > 200) values.shift(); samples.set(stage, values); },
  count(name: "disk_hit" | "disk_miss" | "memory_hit" | "image_open" | "image_error") { counts.set(name, (counts.get(name) || 0) + 1); },
  reset() { samples.clear(); counts.clear(); },
  snapshot() { return { counters: Object.fromEntries(counts), stages: Object.fromEntries([...samples].map(([name, values]) => { const sorted = [...values].sort((a, b) => a - b); return [name, { n: values.length, p50: Math.round(sorted[Math.floor((sorted.length - 1) * .5)]), p95: Math.round(sorted[Math.floor((sorted.length - 1) * .95)]) }]; })) }; },
};
export async function timed<T>(stage: Stage, run: () => Promise<T>) { const start = clock(); try { return await run(); } finally { loadingMetrics.record(stage, clock() - start); } }