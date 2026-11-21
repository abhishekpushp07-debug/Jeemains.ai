import { useEffect, useMemo, useState } from "react";
import { api, apiBytes, privateAssets, websiteHomeUrl } from "@/src/api/client";
import { imageGrant } from "./assetGrants";
import { originalImageValue } from "./imageDownload";
import { saveImage } from "./deviceCache/cache";
import { PaperQuestion, questionPaths } from "./paperAssets";
import { piecesOf } from "./pieces";

// The whole paper's question pictures in a few requests (website contract, /attempts/{id}/assets/pack):
// 4-byte big-endian header length, JSON header {total, items:[{question_id, kind, index, size}]}, then the picture bytes in order.
// /assets/links gives the same parts as public CDN links; a part that fails there comes through our server instead.
// look=cut: a question the website supplies in cut pieces sends them (kind "piece") in place of its whole picture.
const PART = 12;
type Links = { total: number; limit: number; parts: string[] };

const mimeOf = (b: Uint8Array) => b[0] === 0xff && b[1] === 0xd8 ? "image/jpeg" : b[0] === 0x52 && b[1] === 0x49 ? "image/webp" : "image/png";

function readPack(bytes: Uint8Array) {
  const n = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(0);
  if (n <= 0 || n > 65536 || 4 + n > bytes.length) throw new Error("Paper part incomplete");
  const header = JSON.parse(new TextDecoder().decode(bytes.subarray(4, 4 + n)));
  if (!header || !Array.isArray(header.items)) throw new Error("Paper part unreadable");
  return { total: Number(header.total) || 0, items: header.items as { question_id: string; kind?: string; index: number; size: number }[], start: 4 + n };
}

async function cdnPart(url: string, signal: AbortSignal) {
  const ctl = new AbortController(), stop = () => ctl.abort();
  signal.addEventListener("abort", stop, { once: true });
  const timer = setTimeout(stop, 20000);
  try {
    const res = await fetch(url.startsWith("/") ? new URL(url, websiteHomeUrl()).href : url, { credentials: "omit", signal: ctl.signal });
    if (!res.ok) throw new Error("Paper part " + res.status);
    return new Uint8Array(await res.arrayBuffer());
  } finally { clearTimeout(timer); signal.removeEventListener("abort", stop); }
}

/** Every picture of the part goes into the private image cache (and the encrypted phone copy), as if downloaded one by one. */
async function keepPart(id: string, bytes: Uint8Array, signal: AbortSignal, got: Set<string>) {
  const { total, items, start } = readPack(bytes);
  let at = start;
  for (const item of items) {
    const size = Number(item.size) || 0;
    const path = `/attempts/${encodeURIComponent(id)}/questions/${encodeURIComponent(item.question_id)}/asset/${item.kind === "piece" ? "piece" : "question"}/${Number(item.index)}`;
    const grant = imageGrant(path);
    if (signal.aborted) return total;
    if (grant && !got.has(path) && size > 0 && at + size <= bytes.length) {
      const picture = bytes.slice(at, at + size);
      const image = { bytes: picture, mime: mimeOf(picture), etag: "", modified: "", at: Date.now() };
      const value = await originalImageValue(image, signal);
      if (imageGrant(path) === grant) {
        grant.validated = true;
        if (privateAssets.adopt(path, value)) void saveImage(grant.contentKey, image);
        got.add(path);
      } else value.dispose?.();
    }
    at += size;
  }
  return total;
}

async function loadPack(id: string, cut: boolean, got: Set<string>, signal: AbortSignal, changed: () => void) {
  const base = `/attempts/${encodeURIComponent(id)}/assets`;
  const links = await api<Links>(`${base}/links${cut ? "?look=cut" : ""}`, { signal }).catch(() => null);
  const parts = links && links.limit === PART && Array.isArray(links.parts) ? links.parts : null;
  let total = Number(links?.total) || Infinity, next = 0, failed = false;
  const part = async (k: number) => {
    let bytes: Uint8Array | null = parts?.[k] ? await cdnPart(parts[k], signal).catch(() => null) : null;
    if (signal.aborted) return;
    if (!bytes) bytes = await apiBytes(`${base}/pack?offset=${k * PART}&limit=${PART}${cut ? "&look=cut" : ""}`);
    const told = await keepPart(id, bytes, signal, got);
    if (!Number.isFinite(total)) total = told;
    changed();
  };
  // Without the links answer the first part tells how many pictures there are.
  if (!Number.isFinite(total)) await part(next++);
  // A cut paper has several times more (small) pictures: two parts at a time, as the website does.
  // A paper without pieces (every PYQ paper) loads one part after the other, as it always has.
  const worker = async () => {
    while (!failed && !signal.aborted && next * PART < total) await part(next++).catch(e => { failed = true; throw e; });
  };
  await Promise.all(cut ? [worker(), worker()] : [worker()]);
}

/** Get-ready minute: loads the whole paper's question pictures; anything the pack misses goes through the normal image queue. */
export function usePaperPack(id: string, rows: PaperQuestion[], active: boolean) {
  const paths = useMemo(() => rows.flatMap(q => questionPaths(id, q)), [id, rows]);
  const cut = useMemo(() => rows.some(piecesOf), [rows]);
  const [done, setDone] = useState(0);
  useEffect(() => {
    if (!active || !paths.length) return;
    const ctl = new AbortController(), got = new Set<string>();
    const count = () => { for (const p of paths) if (privateAssets.status(p) === "ready") got.add(p); setDone(got.size); };
    const rest = () => { if (!ctl.signal.aborted) privateAssets.preload(paths.filter(p => !got.has(p))); };
    count();
    const timer = setInterval(count, 500);
    if (got.size < paths.length) void loadPack(id, cut, got, ctl.signal, count).then(rest, rest);
    return () => { ctl.abort(); clearInterval(timer); };
  }, [id, paths, cut, active]);
  return { done: Math.min(done, paths.length), total: paths.length };
}
