export class RequestDeadlineError extends Error {
  constructor() { super("Request deadline exceeded"); this.name = "RequestDeadlineError"; }
}
const cancelled = () => Object.assign(new Error("Request cancelled"), { name: "AbortError" });
/** Deadline includes headers AND body, even if a platform body reader ignores abort. */
export async function requestDeadline<T>(run: (signal: AbortSignal) => Promise<T>, ms: number, caller?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let stop = () => {};
  const interrupted = new Promise<never>((_, reject) => {
    stop = () => { controller.abort(); reject(cancelled()); };
    if (caller?.aborted) { stop(); return; }
    caller?.addEventListener("abort", stop, { once: true });
    timer = setTimeout(() => { controller.abort(); reject(new RequestDeadlineError()); }, ms);
  });
  try {
    return await Promise.race([interrupted, Promise.resolve().then(() => { if (controller.signal.aborted) throw cancelled(); return run(controller.signal); })]);
  } finally { clearTimeout(timer); caller?.removeEventListener("abort", stop); }
}