import { useEffect, useMemo, useState } from "react";
import { api, apiBytes, onAssetScopeReset, privateAssets, websiteHomeUrl } from "@/src/api/client";
import { imageGrant } from "./assetGrants";
import { originalImageValue } from "./imageDownload";
import { saveImage, savedImages } from "./deviceCache/cache";
import { imagePaths, PaperQuestion, partLoads, questionPaths } from "./paperAssets";
import { piecesOf } from "./pieces";

// The whole paper's question pictures in a few requests (website contract, /attempts/{id}/assets/pack):
// 4-byte big-endian header length, JSON header {total, items:[{question_id, kind, index, size, etag}]}, then the picture bytes in order.
// /assets/links gives the same parts as public CDN links; a part that fails there comes through our server instead.
// look=cut: a question the website supplies in cut pieces sends them (kind "piece") in place of its whole picture.
// The website's new picture answers (memory/PICTURES_APP.md) add: format=webp (a lighter copy, the same pixels), parts
// for a finished attempt, and kind=solution (every item then says kind "solution").
const PART = 12;
/** A part is fetched only when at least this many of its 12 pictures are missing on this phone. */
const WORTH = 4;
type Links = { total: number; limit: number; parts: string[] };
type Item = { question_id: string; kind?: string | null; index: number; size: number; etag?: unknown };
/** What is asked for and how it is kept. `quiet` (a result): the pictures go to the phone copy only and the image queue
 *  shows them from there, except one a screen is already waiting for. `order`: the pictures expected, in paper order. */
type Ask = { id: string; version: string; solution: boolean; cut: boolean; webp: boolean; quiet?: boolean; order?: string[] };

const mimeOf = (b: Uint8Array) => b[0] === 0xff && b[1] === 0xd8 ? "image/jpeg" : b[0] === 0x52 && b[1] === 0x49 ? "image/webp" : "image/png";
// The item's etag is the one-picture route's ETag for the same picture and format: the phone copy can be re-checked with it.
const etagOf = (v: unknown) => typeof v === "string" && v ? (/^(W\/)?"/.test(v) ? v : `"${v}"`) : "";
const words = (a: Ask) => [a.cut && "look=cut", a.solution && "kind=solution", a.webp && "format=webp", a.version !== "original" && `score_version=${encodeURIComponent(a.version)}`].filter(Boolean).join("&");
// The third number of a part's name says what the part holds (8 = solutions). Read from the answer, never assumed.
const flagsOf = (part: unknown) => Number(/\/\d+-\d+-(\d+)-[^/]*$/.exec(String(part))?.[1]) || 0;
// A picture is a solution only when its item says so: a website still giving its old answers ignores kind=solution and
// sends the question pictures. An item of another kind than the one asked for is left out.
function itemPath(a: Ask, item: Item) {
  const kind = a.solution ? (item.kind === "solution" ? "solution" : "") : item.kind === "piece" ? "piece" : item.kind == null || item.kind === "question" ? "question" : "";
  return kind && `/attempts/${encodeURIComponent(a.id)}/questions/${encodeURIComponent(item.question_id)}/asset/${kind}/${Number(item.index)}${a.version === "original" ? "" : `?score_version=${encodeURIComponent(a.version)}`}`;
}

function readPack(bytes: Uint8Array) {
  const n = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(0);
  if (n <= 0 || n > 65536 || 4 + n > bytes.length) throw new Error("Paper part incomplete");
  const header = JSON.parse(new TextDecoder().decode(bytes.subarray(4, 4 + n)));
  if (!header || !Array.isArray(header.items)) throw new Error("Paper part unreadable");
  return { total: Number(header.total) || 0, items: header.items as Item[], start: 4 + n };
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
async function keepPart(a: Ask, bytes: Uint8Array, signal: AbortSignal, got: Set<string>) {
  const { total, items, start } = readPack(bytes);
  if (a.solution && items.length && !items.some(item => item.kind === "solution")) throw new Error("These parts hold no solutions");
  let at = start;
  for (const item of items) {
    const size = Number(item.size) || 0;
    const path = itemPath(a, item);
    const grant = path ? imageGrant(path) : undefined;
    if (signal.aborted) return total;
    if (grant && !got.has(path) && size > 0 && at + size <= bytes.length) {
      const picture = bytes.slice(at, at + size);
      const image = { bytes: picture, mime: mimeOf(picture), etag: etagOf(item.etag), modified: "", at: Date.now() };
      const state = a.quiet ? privateAssets.status(path) : "loading";
      if (state === "loading") {
        const value = await originalImageValue(image, signal);
        if (imageGrant(path) === grant) {
          grant.validated = true;
          if (privateAssets.adopt(path, value)) void saveImage(grant.contentKey, image);
          got.add(path);
        } else value.dispose?.();
      } else {
        // Written before the next part is fetched, so a slow phone never holds more than one part in memory.
        if (state !== "ready") await saveImage(grant.contentKey, image);
        got.add(path);
      }
    }
    at += size;
  }
  return total;
}

async function loadPack(a: Ask, got: Set<string>, signal: AbortSignal, changed: () => void, workers: number) {
  const base = `/attempts/${encodeURIComponent(a.id)}/assets`, q = words(a);
  let links: Links | null = null;
  // 403 / 409: these pictures are not given in parts (solutions not released yet, or the old answer for a finished attempt).
  try { links = await api<Links>(`${base}/links${q ? `?${q}` : ""}`, { signal }); } catch (e: any) { if (e?.status === 403 || e?.status === 409) throw e; }
  const parts = links && links.limit === PART && Array.isArray(links.parts) ? links.parts : null;
  if (a.solution && parts?.length && !(flagsOf(parts[0]) & 8)) throw new Error("These parts hold no solutions");
  let total = Number(links?.total) || Infinity, next = 0, failed = false;
  // A part is worth fetching when 4 of its pictures are missing here (or all of them, in a short last part).
  const worth = (k: number) => {
    if (!a.order || total !== a.order.length) return true;
    const mine = a.order.slice(k * PART, (k + 1) * PART);
    return mine.filter(p => !got.has(p)).length >= Math.min(WORTH, mine.length);
  };
  const part = async (k: number) => {
    if (!worth(k)) return;
    let bytes: Uint8Array | null = parts?.[k] ? await cdnPart(parts[k], signal).catch(() => null) : null;
    if (signal.aborted) return;
    if (!bytes) bytes = await apiBytes(`${base}/pack?offset=${k * PART}&limit=${PART}${q ? `&${q}` : ""}`);
    const told = await keepPart(a, bytes, signal, got);
    if (!Number.isFinite(total)) total = told;
    changed();
  };
  // Without the links answer the first part tells how many pictures there are.
  if (!Number.isFinite(total)) await part(next++);
  const worker = async () => {
    while (!failed && !signal.aborted && next * PART < total) await part(next++).catch(e => { failed = true; throw e; });
  };
  await Promise.all(Array.from({ length: workers }, worker));
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
    // Step 5: the lighter copies, only when every row carries the website's asset_revision and the owner's switch says so.
    const webp = paths.every(p => (imageGrant(p)?.step || 0) >= 5);
    // A cut paper has several times more (small) pictures: two parts at a time, as the website does.
    // A paper without pieces (every PYQ paper) loads one part after the other, as it always has.
    if (got.size < paths.length) void loadPack({ id, version: "original", solution: false, cut, webp }, got, ctl.signal, count, cut ? 2 : 1).then(rest, rest);
    return () => { ctl.abort(); clearInterval(timer); };
  }, [id, paths, cut, active]);
  return { done: Math.min(done, paths.length), total: paths.length };
}

/** A released result, with the website's new picture answers only: the pictures this phone does not have yet come in
 *  parts of 12 (step 3: questions; step 4: solutions too; step 5: as lighter copies) and are kept on the phone. The
 *  picture on screen is still loaded on its own, at once. Whatever the parts do not bring is handed to the image queue,
 *  one by one, as always. False: not for this result; the caller loads everything one by one. */
export function loadResultPictures(id: string, rows: PaperQuestion[], version = "original") {
  const key = `${id}|${version}`, cut = rows.some(piecesOf);
  const kinds = [false, true].map(solution => ({ solution, paths: rows.flatMap(q => solution ? imagePaths(id, q, "solution", version) : questionPaths(id, q, version)) }));
  const all = kinds.flatMap(k => k.paths);
  const step = all.reduce((least, p) => Math.min(least, imageGrant(p)?.step || 0), 9);
  if (!all.length || step < 3) return false;
  if (partLoads.has(key)) return true;
  partLoads.add(key);
  const ctl = new AbortController(), got = new Set<string>();
  const forget = onAssetScopeReset(() => ctl.abort());
  const here = () => !ctl.signal.aborted && privateAssets.isGroup(id);
  (async () => {
    const kept = await savedImages(all.map(p => imageGrant(p)?.contentKey || ""));
    if (!kept || !here()) return; // a phone that keeps no copies: one by one
    all.forEach((p, i) => { if (kept[i]) got.add(p); });
    const asks = kinds.filter(k => (!k.solution || step >= 4) && k.paths.filter(p => !got.has(p)).length >= WORTH);
    await Promise.all(asks.map(k => loadPack({ id, version, solution: k.solution, cut: cut && !k.solution, webp: step >= 5, quiet: true, order: k.paths }, got, ctl.signal,
      () => { if (!here()) ctl.abort(); }, asks.length > 1 ? 1 : 2).catch(() => {})));
  })().catch(() => {}).finally(() => {
    forget(); partLoads.delete(key);
    if (here()) privateAssets.preload(all.filter(p => !got.has(p)));
  });
  return true;
}
