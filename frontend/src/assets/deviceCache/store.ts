import { Directory, File, Paths } from "expo-file-system";
import * as SecureStore from "expo-secure-store";
import { AESEncryptionKey, AESSealedData, aesEncryptAsync, aesDecryptAsync } from "expo-crypto";
import { DeviceStore, DISK_BUDGET, MAX_IMAGE, serialOperations } from "./types";

const KEY = "jeelive.private-images.v1";
const root = () => new Directory(Paths.cache, "jeelive-private-images-v1");
const serial = serialOperations();
let scope = "", key: AESEncryptionKey | null = null;
let index: Record<string, { size: number; used: number }> = {};
const aad = (owner: string, id: string) => new TextEncoder().encode(`jeelive-images-v1|${owner}|${id}`);

async function reset() {
  key = null; scope = ""; index = {};
  const dir = root(); if (dir.exists) await dir.delete();
  await SecureStore.deleteItemAsync(KEY);
}
async function saveIndex() {
  const temp = new File(root(), "index.tmp"), file = new File(root(), "index.json");
  await temp.write(JSON.stringify(index)); await temp.move(file, { overwrite: true });
}
async function remove(id: string) {
  const file = new File(root(), `${id}.bin`); if (file.exists) await file.delete(); delete index[id];
}
export const deviceStore: DeviceStore = {
  open: owner => serial(async () => {
    if (scope === owner && key) return;
    let saved: { scope: string; key: string } | null = null;
    try { saved = JSON.parse(await SecureStore.getItemAsync(KEY) || "null"); } catch { /* rotate corrupt key */ }
    if (!saved || saved.scope !== owner) {
      await reset(); key = await AESEncryptionKey.generate();
      saved = { scope: owner, key: await key.encoded("hex") };
      await SecureStore.setItemAsync(KEY, JSON.stringify(saved), { keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY });
    } else key = await AESEncryptionKey.import(saved.key, "hex");
    scope = owner; await root().create({ intermediates: true, idempotent: true });
    try {
      const savedIndex = await new File(root(), "index.json").json();
      index = Object.fromEntries(Object.entries(savedIndex || {}).filter(([id, value]) => {
        const v = value as any; return /^[a-f0-9]{64}$/.test(id) && Number.isFinite(v?.size) && v.size > 0 && v.size <= MAX_IMAGE + 8192 && Number.isFinite(v?.used);
      })) as typeof index;
    } catch { index = {}; }
    // No source URLs, private text or unencrypted image bytes are ever written.
    const keep = new Set(Object.keys(index).filter(id => /^[a-f0-9]{64}$/.test(id)));
    for (const item of root().list()) if (item instanceof File && (item.name.endsWith(".tmp") || (item.name.endsWith(".bin") && !keep.has(item.name.slice(0, -4))))) await item.delete();
  }),
  read: (owner, id) => serial(async () => {
    if (owner !== scope || !key || !/^[a-f0-9]{64}$/.test(id) || !index[id]) return null;
    const file = new File(root(), `${id}.bin`);
    try {
      if (!file.exists || file.size > MAX_IMAGE + 8192) throw new Error("Missing or oversized cache file");
      const plain = await aesDecryptAsync(AESSealedData.fromCombined(await file.bytes()), key, { additionalData: aad(owner, id) });
      index[id].used = Date.now(); return plain;
    } catch { await remove(id); await saveIndex(); return null; }
  }),
  write: (owner, id, bytes) => serial(async () => {
    if (scope !== owner || !key || bytes.length > MAX_IMAGE + 4096 || !/^[a-f0-9]{64}$/.test(id)) return;
    const sealed = await aesEncryptAsync(bytes, key, { additionalData: aad(owner, id) });
    const encrypted = await sealed.combined();
    let total = Object.values(index).reduce((n, v) => n + v.size, 0) - (index[id]?.size || 0);
    for (const [old, entry] of Object.entries(index).sort((a, b) => a[1].used - b[1].used)) {
      if (total + encrypted.length <= DISK_BUDGET) break;
      if (old !== id) { await remove(old); total -= entry.size; }
    }
    const temp = new File(root(), `${id}.tmp`), file = new File(root(), `${id}.bin`);
    await temp.write(encrypted); await temp.move(file, { overwrite: true });
    index[id] = { size: encrypted.length, used: Date.now() }; await saveIndex();
  }),
  remove: (owner, id) => serial(async () => { if (owner === scope) { await remove(id); await saveIndex(); } }),
  clear: () => serial(reset),
};