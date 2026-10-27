export type AssetValue = { uri: string; bytes: number; dispose?: () => void };
type Job = { path: string; priority: number; generation: number; ctl: AbortController; promise: Promise<string>; resolve: (uri: string) => void; reject: (e: unknown) => void; running: boolean };
export type AssetProgress = { total: number; ready: number; failed: number; queued: number; limited: boolean };
const cancelled = () => Object.assign(new Error("Private image loading stopped."), { name: "AbortError" });

/** No disk, account IDs, answers or credentials. One bounded private session cache. */
export class PrivateAssetQueue {
  private cache = new Map<string, AssetValue>();
  private jobs = new Map<string, Job>();
  private failures = new Map<string, { error: unknown; after: number }>();
  private listeners = new Set<() => void>();
  private generation = 0;
  private active = 0;
  private bytes = 0;
  private revision = 0;
  private notification: ReturnType<typeof setTimeout> | undefined;
  private admitted = new Set<string>();
  private group = "";
  private enabled = true;
  private pinned = new Set<string>();
  constructor(private load: (path: string, signal: AbortSignal) => Promise<AssetValue>, readonly concurrency = 6, readonly maxBytes = 48 * 1024 * 1024, private permitted = (_path: string) => true) {}
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  snapshot = () => this.revision;
  private notify() {
    this.revision++;
    if (!this.notification) this.notification = setTimeout(() => { this.notification = undefined; this.listeners.forEach(fn => fn()); }, 0);
  }
  peek(path: string) { return this.cache.get(path)?.uri; }
  isGroup(group: string) { return group === this.group; }
  pin(paths: string[]) { this.pinned = new Set(paths); }
  invalidate(path: string) {
    const old = this.cache.get(path); if (old) { old.dispose?.(); this.bytes -= old.bytes; this.cache.delete(path); }
    const job = this.jobs.get(path); if (job) { job.ctl.abort(); this.jobs.delete(path); job.reject(cancelled()); }
    this.failures.delete(path); this.admitted.delete(path); this.notify();
  }
  status(path: string) { return this.cache.has(path) ? "ready" : this.failures.has(path) ? "failed" : this.jobs.has(path) ? "loading" : "idle"; }
  progress(paths: string[]): AssetProgress {
    let ready = 0, failed = 0, queued = 0;
    for (const path of paths) { const state = this.status(path); if (state === "ready") ready++; else if (state === "failed") failed++; else if (state === "loading") queued++; }
    const evicted = paths.some(path => this.admitted.has(path) && this.status(path) === "idle");
    return { total: paths.length, ready, failed, queued, limited: evicted || (paths.length > ready + failed + queued && this.bytes >= this.maxBytes * .9) };
  }
  selectGroup(group: string) {
    if (group === this.group) return;
    this.group = group; this.admitted.clear(); this.pinned.clear();
    for (const job of [...this.jobs.values()]) {
      if (job.priority < 100) { job.ctl.abort(); this.jobs.delete(job.path); job.reject(cancelled()); }
    }
    this.notify();
  }
  preload(paths: string[]) {
    if (!this.enabled) return;
    // Jobs contain paths only. Encrypted disk persistence lets the entire paper
    // finish downloading even when older decoded images leave the RAM window.
    for (const path of paths) {
      if (this.admitted.has(path) || this.cache.has(path)) continue;
      this.admitted.add(path);
      void this.get(path, 10).catch(() => {});
    }
  }
  retry(paths: string[]) {
    for (const path of paths) { const fail = this.failures.get(path); if (fail && Date.now() >= fail.after) { this.failures.delete(path); this.admitted.delete(path); } }
    this.preload(paths); this.notify();
  }
  get(path: string, priority = 100): Promise<string> {
    if (!this.enabled || !this.permitted(path)) return Promise.reject(cancelled());
    const cached = this.cache.get(path);
    if (cached) { this.cache.delete(path); this.cache.set(path, cached); return Promise.resolve(cached.uri); }
    const old = this.jobs.get(path);
    if (old) { old.priority = Math.max(old.priority, priority); this.pump(); return old.promise; }
    const failed = this.failures.get(path);
    if (failed && Date.now() < failed.after) return Promise.reject(failed.error);
    this.failures.delete(path);
    let resolve!: (uri: string) => void, reject!: (e: unknown) => void;
    const promise = new Promise<string>((yes, no) => { resolve = yes; reject = no; });
    this.jobs.set(path, { path, priority, generation: this.generation, ctl: new AbortController(), promise, resolve, reject, running: false });
    this.notify(); this.pump(); return promise;
  }
  private pump() {
    while (this.active < this.concurrency) {
      const job = [...this.jobs.values()].filter(j => !j.running).sort((a, b) => b.priority - a.priority)[0];
      if (!job) return;
      // Reserve one network slot for a question the student jumps to.
      if (job.priority < 100 && this.active >= this.concurrency - 1) return;
      job.running = true; this.active++;
      this.load(job.path, job.ctl.signal).then(value => {
        if (job.generation !== this.generation || job.ctl.signal.aborted) { value.dispose?.(); throw cancelled(); }
        // Account for URI memory, and release browser object URLs upon eviction.
        while (this.bytes + value.bytes > this.maxBytes && this.cache.size) {
          const oldest = [...this.cache.entries()].find(([path]) => !this.pinned.has(path));
          if (!oldest) break;
          this.cache.delete(oldest[0]); this.bytes -= oldest[1].bytes; oldest[1].dispose?.();
        }
        if (this.bytes + value.bytes > this.maxBytes) { value.dispose?.(); throw new Error("This source image exceeds safe image memory. Close other papers and retry."); }
        this.cache.set(job.path, value); this.bytes += value.bytes;
        job.resolve(value.uri);
      }).catch(e => {
        if (!job.ctl.signal.aborted && job.generation === this.generation) this.failures.set(job.path, { error: e, after: Date.now() + Math.max(e?.retryAfterMs || 0, e?.status === 429 ? 30000 : 0) });
        job.reject(e);
      }).finally(() => {
        this.active--;
        if (this.jobs.get(job.path) === job) this.jobs.delete(job.path);
        this.notify(); this.pump();
      });
    }
  }
  clear() {
    this.generation++;
    for (const job of this.jobs.values()) { job.ctl.abort(); job.reject(cancelled()); }
    this.jobs.clear();
    for (const value of this.cache.values()) value.dispose?.();
    this.cache.clear(); this.failures.clear(); this.admitted.clear(); this.pinned.clear(); this.bytes = 0; this.group = "";
    this.notify();
  }
  pause() { this.enabled = false; this.clear(); }
  resume() { this.enabled = true; }
}