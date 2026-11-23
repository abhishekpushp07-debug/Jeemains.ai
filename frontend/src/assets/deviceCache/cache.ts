import { digestStringAsync, CryptoDigestAlgorithm } from "expo-crypto";
import { deviceStore } from "./store";
import { packImage, SavedImage, unpackImage } from "./types";

let scope = "", generation = 0;
let ready: Promise<void> = Promise.resolve();
const writing = new Map<string, Promise<void>>();
const hashes = new Map<string, Promise<string>>();
const hash = (text: string) => digestStringAsync(CryptoDigestAlgorithm.SHA256, text);
function imageId(text: string) {
  let result = hashes.get(text);
  if (!result) { result = hash(text); hashes.set(text, result); if (hashes.size > 512) hashes.delete(hashes.keys().next().value!); void result.catch(() => hashes.delete(text)); }
  return result;
}
export function configureImageDisk(account: string, origin: string) {
  const epoch = ++generation;
  scope = ""; hashes.clear();
  ready = (async () => { const next = await hash(`${origin}|${account}`); if (epoch !== generation) return; scope = next; await deviceStore.open(next); })().catch(() => { if (epoch === generation) scope = ""; });
}
export function purgeImageDisk() {
  generation++; scope = ""; writing.clear(); hashes.clear();
  ready = deviceStore.clear().catch(() => {});
}
export async function readSavedImage(contentKey: string): Promise<SavedImage | null> {
  try {
    const epoch = generation; await ready;
    if (!scope || epoch !== generation) return null;
    await writing.get(contentKey);
    if (epoch !== generation) return null;
    const owner = scope, id = await imageId(contentKey);
    if (epoch !== generation) return null;
    const data = await deviceStore.read(owner, id);
    if (!data || epoch !== generation) return null;
    try { return unpackImage(data); } catch { await deviceStore.remove(owner, id); return null; }
  } catch { return null; } // Quota/private mode falls back to memory, never plaintext.
}
/** Which of these pictures already have a copy on this phone. Null: the phone keeps no copies (no storage). */
export async function savedImages(contentKeys: string[]): Promise<boolean[] | null> {
  try {
    const epoch = generation; await ready;
    if (!scope || epoch !== generation) return null;
    const kept = await deviceStore.keys(scope), ids = await Promise.all(contentKeys.map(imageId));
    return epoch === generation ? contentKeys.map((key, i) => writing.has(key) || kept.has(ids[i])) : null;
  } catch { return null; }
}
async function persistImage(contentKey: string, image: SavedImage) {
  const epoch = generation; await ready;
  if (!scope || epoch !== generation) return;
  const owner = scope, id = await imageId(contentKey);
  if (epoch !== generation) return;
  try { await deviceStore.write(owner, id, packImage(image)); } catch { /* optional cache cannot block original paper */ }
}
export function saveImage(contentKey: string, image: SavedImage): Promise<void> {
  const pending = writing.get(contentKey); if (pending) return pending;
  const job = persistImage(contentKey, image).catch(() => {}).finally(() => { if (writing.get(contentKey) === job) writing.delete(contentKey); });
  writing.set(contentKey, job); return job;
}