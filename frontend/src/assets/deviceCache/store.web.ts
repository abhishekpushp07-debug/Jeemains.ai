import { DeviceStore, DISK_BUDGET, MAX_IMAGE, serialOperations } from "./types";

type Entry = { id: string; iv: Uint8Array; cipher: ArrayBuffer; size: number; used: number };
const serial = serialOperations();
let db: IDBDatabase | null = null, scope = "", key: CryptoKey | null = null;
const bytes = (data: Uint8Array) => data.slice().buffer as ArrayBuffer;
const aad = (owner: string, id: string) => bytes(new TextEncoder().encode(`jeelive-images-v1|${owner}|${id}`));
async function connect() {
  if (db) return db;
  if (!globalThis.crypto?.subtle || !globalThis.indexedDB) throw new Error("Encrypted local storage unavailable");
  db = await new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("jeelive-private-images-v1", 2);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains("meta")) request.result.createObjectStore("meta");
      if (!request.result.objectStoreNames.contains("images")) request.result.createObjectStore("images", { keyPath: "id" });
      if (!request.result.objectStoreNames.contains("catalog")) { request.result.createObjectStore("catalog", { keyPath: "id" }); request.transaction?.objectStore("images").clear(); }
    };
    request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
  });
  db.onversionchange = () => { db?.close(); db = null; key = null; scope = ""; };
  return db;
}
async function transaction<T>(store: string, mode: IDBTransactionMode, run: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const database = await connect();
  return new Promise((resolve, reject) => { const tx = database.transaction(store, mode), request = run(tx.objectStore(store)); let result: T;
    request.onsuccess = () => { result = request.result; }; tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error || new Error("Device storage transaction stopped"));
  });
}
async function commit(id: string, entry?: Entry) {
  const database = await connect();
  await new Promise<void>((resolve, reject) => {
    const tx = database.transaction(["images", "catalog"], "readwrite");
    if (entry) { tx.objectStore("images").put(entry); tx.objectStore("catalog").put({ id, size: entry.size, used: entry.used }); }
    else { tx.objectStore("images").delete(id); tx.objectStore("catalog").delete(id); }
    tx.oncomplete = () => resolve(); tx.onerror = tx.onabort = () => reject(tx.error);
  });
}
async function reset() { key = null; scope = ""; await transaction("images", "readwrite", s => s.clear()); await transaction("catalog", "readwrite", s => s.clear()); await transaction("meta", "readwrite", s => s.clear()); }
export const deviceStore: DeviceStore = {
  open: owner => serial(async () => {
    if (owner === scope && key) return;
    const saved = await transaction<any>("meta", "readonly", s => s.get("account"));
    if (!saved || saved.scope !== owner) {
      await reset();
      key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
      await transaction("meta", "readwrite", s => s.put({ scope: owner, key }, "account"));
    } else key = saved.key;
    scope = owner;
  }),
  read: (owner, id) => serial(async () => {
    if (owner !== scope || !key) return null;
    const record = await transaction<Entry | undefined>("images", "readonly", s => s.get(id));
    if (!record) return null;
    try {
      const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: bytes(record.iv), additionalData: aad(owner, id) }, key, record.cipher);
      await transaction("catalog", "readwrite", s => s.put({ id, size: record.size, used: Date.now() }));
      return new Uint8Array(plain);
    } catch { await commit(id); return null; }
  }),
  write: (owner, id, plain) => serial(async () => {
    if (owner !== scope || !key || plain.length > MAX_IMAGE + 4096) return;
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const cipher = await crypto.subtle.encrypt({ name: "AES-GCM", iv: bytes(iv), additionalData: aad(owner, id) }, key, bytes(plain));
    const entries = await transaction<{ id: string; size: number; used: number }[]>("catalog", "readonly", s => s.getAll());
    let total = entries.reduce((n, e) => n + (e.id === id ? 0 : e.size), 0);
    for (const e of entries.sort((a, b) => a.used - b.used)) {
      if (total + cipher.byteLength <= DISK_BUDGET) break;
      if (e.id !== id) { await commit(e.id); total -= e.size; }
    }
    await commit(id, { id, iv, cipher, used: Date.now(), size: cipher.byteLength });
  }),
  remove: (owner, id) => serial(async () => { if (owner === scope) await commit(id); }),
  clear: () => serial(reset),
};