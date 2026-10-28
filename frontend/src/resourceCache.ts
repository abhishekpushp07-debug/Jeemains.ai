/** Small, account-resettable JSON cache + shared in-flight reads. No image bytes/auth. */
type Entry = { value: any; at: number; bytes: number };
type Load = (signal: AbortSignal) => Promise<any>;
type Pending = { promise: Promise<any>; controller: AbortController };
type Store = (key: string, raw: string, at: number) => void;
const MAX_BYTES = 2 * 1024 * 1024;
const MAX_ITEM = 384 * 1024;
// A short, account-keyed list window removes duplicate navigation reads. Actions
// still recheck the server; explicit refresh and attempt mutations invalidate it.
const freshFor = (key: string) => key.startsWith("rf.catalog.") ? 60000 :
  /^u\.[^.]+\.(pyq\.jee-main$|\/exam-navigation\/[^/]+\/catalogue\?)/.test(key) ? 10000 : 0;

export class ResourceCache {
  private memory = new Map<string, Entry>();
  private flights = new Map<string, Pending>();
  private queue = new Map<string, { load: Load; persist: boolean }>();
  private activeBackground = false;
  private bytes = 0;
  private store?: Store;
  private counters = { loads: 0, coalesced: 0, freshHits: 0, evictions: 0 };

  setPersistence(store: Store) { this.store = store; }
  peek<T>(key: string): T | null {
    const item = this.memory.get(key);
    if (!item) return null;
    if (Date.now() - item.at > 10 * 60 * 1000) { this.remove(key); return null; }
    this.memory.delete(key); this.memory.set(key, item);
    return item.value as T;
  }
  private remove(key: string) {
    this.bytes -= this.memory.get(key)?.bytes || 0;
    this.memory.delete(key);
  }
  private remember(key: string, value: any, persist: boolean) {
    const raw = JSON.stringify(value);
    if (raw === undefined || raw.length * 2 > MAX_ITEM) return;
    this.remove(key);
    const at = Date.now(), bytes = raw.length * 2;
    this.memory.set(key, { value, at, bytes }); this.bytes += bytes;
    while (this.bytes > MAX_BYTES || this.memory.size > 64) {
      this.remove(this.memory.keys().next().value!); this.counters.evictions++;
    }
    if (persist) { try { this.store?.(key, raw, at); } catch { /* Optional cache writes cannot break a successful read. */ } }
  }
  request<T>(key: string, load: Load, persist = true, force = false): Promise<T> {
    this.queue.delete(key); // foreground demand promotes queued speculative work
    const item = this.memory.get(key);
    if (!force && item && Date.now() - item.at < freshFor(key)) {
      this.counters.freshHits++; return Promise.resolve(item.value);
    }
    const existing = this.flights.get(key);
    if (existing) { this.counters.coalesced++; return existing.promise; }
    const controller = new AbortController();
    const pending: Pending = { controller, promise: Promise.resolve(null) };
    this.flights.set(key, pending);
    this.counters.loads++;
    let timer: ReturnType<typeof setTimeout>;
    const cancelled = new Promise<never>((_, reject) => {
      controller.signal.addEventListener("abort", () => reject(Object.assign(new Error("Request stopped."), { name: "AbortError" })), { once: true });
      timer = setTimeout(() => { reject(new Error("The server is taking longer than usual. Please retry.")); controller.abort(); }, 32000);
    });
    pending.promise = Promise.race([Promise.resolve().then(() => {
      if (controller.signal.aborted) throw Object.assign(new Error("Request stopped."), { name: "AbortError" });
      return load(controller.signal);
    }), cancelled])
      .then(value => { if (this.flights.get(key) === pending) this.remember(key, value, persist); return value; })
      .finally(() => { clearTimeout(timer); if (this.flights.get(key) === pending) this.flights.delete(key); });
    return pending.promise;
  }
  prefetch(key: string, load: Load, persist = true) {
    if (this.peek(key) !== null || this.flights.has(key) || this.queue.has(key) || this.queue.size >= 6) return;
    this.queue.set(key, { load, persist });
    this.drain();
  }
  private drain() {
    if (this.activeBackground || !this.queue.size) return;
    const [key, task] = this.queue.entries().next().value!;
    this.activeBackground = true;
    void this.request(key, task.load, task.persist).catch(() => {}).finally(() => {
      this.activeBackground = false; this.drain();
    });
  }
  cancelPrefetch(prefix: string) {
    for (const key of this.queue.keys()) if (key.startsWith(prefix)) this.queue.delete(key);
  }
  invalidate(prefix: string) {
    for (const key of this.memory.keys()) if (key.startsWith(prefix)) this.remove(key);
    for (const [key, pending] of this.flights) if (key.startsWith(prefix)) {
      this.flights.delete(key); pending.controller.abort();
    }
    this.cancelPrefetch(prefix);
  }
  clear() { this.invalidate(""); }
  stats() { return { ...this.counters, entries: this.memory.size, retainedJsonBytes: this.bytes, inFlight: this.flights.size, queued: this.queue.size }; }
}

export const resources = new ResourceCache();