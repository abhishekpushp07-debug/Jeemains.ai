import { ResourceCache } from "../src/resourceCache";

declare const process: any;

function assert(cond: any, message: string) {
  if (!cond) throw new Error(message);
}

async function expectReject(p: Promise<any>, message: string) {
  let failed = false;
  try { await p; } catch { failed = true; }
  assert(failed, message);
}

async function run() {
  // duplicate concurrent reads -> single fetch + coalesced
  {
    const c = new ResourceCache();
    let calls = 0;
    const load = async () => { calls++; await new Promise(r => setTimeout(r, 20)); return { ok: 1 }; };
    const [a, b] = await Promise.all([
      c.request<{ ok: number }>("rf.catalog.JEE.portrait", load),
      c.request<{ ok: number }>("rf.catalog.JEE.portrait", load),
    ]);
    assert(a.ok === 1 && b.ok === 1, "concurrent readers should resolve same value");
    assert(calls === 1, "concurrent readers should trigger single load");
  }

  // force request joins current in-flight read
  {
    const c = new ResourceCache();
    let calls = 0;
    const load = async () => { calls++; await new Promise(r => setTimeout(r, 20)); return { n: calls }; };
    const first = c.request<{ n: number }>("k.force", load, true, false);
    const second = c.request<{ n: number }>("k.force", load, true, true);
    const [v1, v2] = await Promise.all([first, second]);
    assert(v1.n === v2.n, "force request should join existing in-flight load");
    assert(calls === 1, "force request should not duplicate in-flight load");
  }

  // account clear/invalidations abort old in-flight and prevent stale repopulation
  {
    const c = new ResourceCache();
    let resolveLoad: ((v: any) => void) | undefined;
    const load = (signal: AbortSignal) => new Promise((resolve, reject) => {
      signal.addEventListener("abort", () => reject(Object.assign(new Error("aborted"), { name: "AbortError" })));
      resolveLoad = resolve as (v: any) => void;
    });
    const pending = c.request("u.A.rf.catalog", load as any);
    c.clear();
    await expectReject(pending, "clear should abort in-flight request");
    resolveLoad?.({ stale: true });
    await new Promise(r => setTimeout(r, 10));
    assert(c.peek("u.A.rf.catalog") === null, "aborted in-flight should not repopulate stale data");
  }

  // key change/account isolation + rf invalidation scope
  {
    const c = new ResourceCache();
    await c.request("u.A.rf.profile", async () => ({ uid: "A" }));
    await c.request("u.B.rf.profile", async () => ({ uid: "B" }));
    c.invalidate("u.A.rf");
    assert(c.peek<any>("u.A.rf.profile") === null, "invalidate should clear only matching user scope");
    assert(c.peek<any>("u.B.rf.profile")?.uid === "B", "invalidate should not clear other account scope");
  }

  // memory budget and item cap
  {
    const c = new ResourceCache();
    const big = "x".repeat(12_000); // ~24KB per entry
    for (let i = 0; i < 120; i++) {
      await c.request(`k.${i}`, async () => ({ i, big }));
    }
    const stats = c.stats();
    assert(stats.entries <= 64, "cache must cap entries to 64");
    assert(stats.retainedJsonBytes <= 2 * 1024 * 1024, "cache must cap memory to <=2MiB encoded budget");

    const huge = "z".repeat(220_000); // >384KiB encoded
    await c.request("k.huge", async () => ({ huge }));
    assert(c.peek("k.huge") === null, "items >384KiB encoded must not be stored");
  }

  // public RF catalog key uses ttl/fresh hit; private wallet-like key revalidates always
  {
    const c = new ResourceCache();
    let catCalls = 0;
    let walletCalls = 0;
    await c.request("rf.catalog.JEE.portrait", async () => ({ v: ++catCalls }));
    await c.request("rf.catalog.JEE.portrait", async () => ({ v: ++catCalls }));
    assert(catCalls === 1, "rf catalog key should reuse fresh cached data");

    await c.request("u.A.wallet", async () => ({ v: ++walletCalls }));
    await c.request("u.A.wallet", async () => ({ v: ++walletCalls }));
    assert(walletCalls === 2, "private/wallet key must always revalidate");
  }

  // prefetch single lane + queue cap + foreground promotion + route-blur cancellation
  {
    const c = new ResourceCache();
    let active = 0;
    let maxActive = 0;
    const makeLoad = (k: string) => async () => {
      active++; maxActive = Math.max(maxActive, active);
      await new Promise(r => setTimeout(r, 15));
      active--; return { k };
    };
    for (let i = 0; i < 8; i++) c.prefetch(`u.A.prefetch.${i}`, makeLoad(String(i)));
    await new Promise(r => setTimeout(r, 5));
    assert(c.stats().queued <= 6, "background prefetch queue should cap at 6");
    await new Promise(r => setTimeout(r, 140));
    assert(maxActive === 1, "prefetch should run in a single background lane");

    // foreground promotion joins queued/in-flight work for the same key
    const c2 = new ResourceCache();
    let calls = 0;
    const load = async () => { calls++; await new Promise(r => setTimeout(r, 20)); return { ok: true }; };
    c2.prefetch("u.A.prefetch.promote", load);
    await c2.request("u.A.prefetch.promote", load);
    assert(calls === 1, "foreground demand should promote/join queued key");

    // route blur cancellation
    c.cancelPrefetch("u.A.prefetch."); // route blur cancellation
    assert(c.stats().queued === 0, "cancelPrefetch should clear queued user-prefetch keys");
  }

  // timeout path does not spin forever, and errors are not cached
  {
    const c = new ResourceCache();
    const realSetTimeout = globalThis.setTimeout;
    (globalThis as any).setTimeout = ((fn: (...args: any[]) => void, ms?: number, ...args: any[]) => {
      if ((ms || 0) >= 32000) return realSetTimeout(fn as any, 5, ...args);
      return realSetTimeout(fn as any, ms as any, ...args);
    }) as any;
    try {
      await expectReject(c.request("k.timeout", async () => new Promise(() => {})), "timeout request should reject quickly under fake timer");
      assert(c.peek("k.timeout") === null, "timed-out response must not be cached");
      await expectReject(c.request("k.error", async () => { throw new Error("boom"); }), "error response should reject");
      assert(c.peek("k.error") === null, "error response must not be cached");
    } finally {
      (globalThis as any).setTimeout = realSetTimeout;
    }
  }

  console.log("resourceCache_iter46: all checks passed");
}

run().catch((e) => {
  console.error("resourceCache_iter46 failed:", e?.message || e);
  process.exit(1);
});
