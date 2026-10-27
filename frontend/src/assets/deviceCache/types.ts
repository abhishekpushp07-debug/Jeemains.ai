export const DISK_BUDGET = 256 * 1024 * 1024;
export const MAX_IMAGE = 16 * 1024 * 1024;
export type DeviceStore = {
  open: (scope: string) => Promise<void>;
  read: (scope: string, key: string) => Promise<Uint8Array | null>;
  write: (scope: string, key: string, bytes: Uint8Array) => Promise<void>;
  remove: (scope: string, key: string) => Promise<void>;
  clear: () => Promise<void>;
};
export function serialOperations() {
  let tail: Promise<unknown> = Promise.resolve();
  return <T>(fn: () => Promise<T>): Promise<T> => { const job = tail.then(fn, fn); tail = job.catch(() => {}); return job; };
}
export type SavedImage = { mime: string; etag: string; modified: string; bytes: Uint8Array };
export function packImage(image: SavedImage) {
  const header = new TextEncoder().encode(JSON.stringify({ mime: image.mime, etag: image.etag, modified: image.modified, length: image.bytes.length }));
  const out = new Uint8Array(4 + header.length + image.bytes.length);
  new DataView(out.buffer).setUint32(0, header.length);
  out.set(header, 4); out.set(image.bytes, 4 + header.length); return out;
}
export function unpackImage(payload: Uint8Array): SavedImage {
  if (payload.length < 5) throw new Error("Incomplete cached image");
  const n = new DataView(payload.buffer, payload.byteOffset, payload.byteLength).getUint32(0);
  if (n > 4096 || n + 4 >= payload.length) throw new Error("Invalid cached image");
  const header = JSON.parse(new TextDecoder().decode(payload.subarray(4, n + 4)));
  const bytes = payload.slice(4 + n);
  if (!/^image\/(png|jpeg|webp|gif|avif)$/.test(header.mime) || bytes.length !== header.length || bytes.length > MAX_IMAGE) throw new Error("Invalid cached image");
  return { mime: header.mime, etag: typeof header.etag === "string" ? header.etag : "", modified: typeof header.modified === "string" ? header.modified : "", bytes };
}