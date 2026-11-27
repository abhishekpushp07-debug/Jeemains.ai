// The browser's side of ./shelf.ts: the same three calls on IndexedDB (a browser's own small storage is too small for
// 7 MB of cards). A browser that has no IndexedDB (some private windows) answers null / false, like a phone that refuses.
let db: Promise<IDBDatabase> | null = null;
const valid = (name: string) => /^[a-z0-9][a-z0-9._-]{0,79}$/i.test(name);

function open(): Promise<IDBDatabase> {
  return (db ||= new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("jeelive-kept-v1", 1);
    request.onupgradeneeded = () => { request.result.createObjectStore("files"); };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  }).catch((error) => { db = null; throw error; }));
}
async function run<T>(mode: IDBTransactionMode, work: (files: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const database = await open();
  return new Promise<T>((resolve, reject) => {
    const tx = database.transaction("files", mode), request = work(tx.objectStore("files"));
    tx.oncomplete = () => resolve(request.result);
    tx.onerror = tx.onabort = () => reject(tx.error);
  });
}

export const shelf = {
  async read(name: string): Promise<string | null> {
    try { const text = valid(name) ? await run<unknown>("readonly", (files) => files.get(name)) : null; return typeof text === "string" ? text : null; } catch { return null; }
  },
  async write(name: string, text: string): Promise<boolean> {
    try { if (!valid(name)) return false; await run("readwrite", (files) => files.put(text, name)); return true; } catch { return false; }
  },
  async remove(name: string): Promise<void> {
    try { if (valid(name)) await run("readwrite", (files) => files.delete(name)); } catch { /* nothing to remove */ }
  },
};
