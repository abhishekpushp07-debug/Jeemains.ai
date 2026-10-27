/** Reads overtake queued encryption, but NEVER cross an open/clear barrier. */
export function priorityOperations() {
  type Job = { run: () => Promise<void>; priority: number; barrier: boolean };
  const waiting: Job[] = [];
  let active = false;
  const pump = () => {
    if (active || !waiting.length) return;
    const barrier = waiting.findIndex(job => job.barrier);
    let next = 0;
    for (let i = 1; i < (barrier < 0 ? waiting.length : barrier); i++) if (waiting[i].priority > waiting[next].priority) next = i;
    const job = waiting.splice(next, 1)[0]; active = true;
    void job.run().finally(() => { active = false; pump(); });
  };
  return <T>(fn: () => Promise<T>, priority = 0, barrier = false): Promise<T> => new Promise<T>((resolve, reject) => {
    waiting.push({ priority, barrier, run: async () => { try { resolve(await fn()); } catch (e) { reject(e); } } });
    pump();
  });
}