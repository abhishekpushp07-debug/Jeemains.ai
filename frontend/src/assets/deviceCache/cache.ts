import { digestStringAsync, CryptoDigestAlgorithm } from "expo-crypto";
import { deviceStore } from "./store";
import { packImage, SavedImage, unpackImage } from "./types";

let scope = "", generation = 0;
let ready: Promise<void> = Promise.resolve();
const writing = new Map<string, Promise<void>>();
const hash = (text: string) => digestStringAsync(CryptoDigestAlgorithm.SHA256, text);
export function configureImageDisk(account: string, origin: string) {
  const epoch = ++generation;
  ready = (async () => { const next = await hash(`${origin}|${account}`); if (epoch !== generation) return; scope = next; await deviceStore.open(next); })().catch(() => { if (epoch === generation) scope = ""; });
}
export function purgeImageDisk() {
  generation++; scope = ""; writing.clear();
  ready = deviceStore.clear().catch(() => {});
}
export async function readSavedImage(contentKey: string): Promise<SavedImage | null> {
  try {
    const epoch = generation; await ready;
    if (!scope || epoch !== generation) return null;
    await writing.get(contentKey);
    if (epoch !== generation) return null;
    const owner = scope, id = await hash(contentKey);
    const data = await deviceStore.read(owner, id);
    if (!data || epoch !== generation) return null;
    try { return unpackImage(data); } catch { await deviceStore.remove(owner, id); return null; }
  } catch { return null; } // Quota/private mode falls back to memory, never plaintext.
}
async function persistImage(contentKey: string, image: SavedImage) {
  const epoch = generation; await ready;
  if (!scope || epoch !== generation) return;
  const owner = scope, id = await hash(contentKey);
  if (epoch !== generation) return;
  try { await deviceStore.write(owner, id, packImage(image)); } catch { /* optional cache cannot block original paper */ }
}
export function saveImage(contentKey: string, image: SavedImage): Promise<void> {
  const pending = writing.get(contentKey); if (pending) return pending;
  const job = persistImage(contentKey, image).catch(() => {}).finally(() => { if (writing.get(contentKey) === job) writing.delete(contentKey); });
  writing.set(contentKey, job); return job;
}