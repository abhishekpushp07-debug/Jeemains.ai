import { Piece, piecesOf } from "./pieces";

type Question = { id: string; asset_count?: number; solution_asset_count?: number; asset_revision?: unknown; source_revision?: unknown; source_ref?: unknown; pieces?: Piece[] | null };
/** `step`: how much of the website's new picture way this picture uses. It is the owner's switch
 *  (backend/app_switches.py) for a row that carries the website's asset_revision, and 0 for every other row:
 *  0 = loaded as every build so far loads it; 2 = a copy kept on this phone under the revision is the picture itself and
 *  is not asked about again; 3 = a result's question pictures come in parts; 4 = its solutions too;
 *  5 = the picture is asked for as a lighter WebP copy. */
export type ImageGrant = { contentKey: string; validated: boolean; step: number; plain?: boolean };
const grants = new Map<string, ImageGrant>();
export const imageGrant = (path: string) => grants.get(path);
export const clearImageGrants = () => grants.clear();
/** A picture this phone could not draw: its next try leaves the kept copy aside and downloads the plain picture
 *  (the PNG every build so far has shown), which then replaces the kept copy. */
export const drawAsPlain = (path: string) => { const grant = grants.get(path); if (grant) grant.plain = true; };
/** A result read from the copy this phone keeps (src/offline/papers.ts): the pictures kept with it are its pictures,
 *  so they are shown without asking the server again (without a line nothing can be asked). */
export function trustKept(attempt: string) {
  const prefix = `/attempts/${encodeURIComponent(attempt)}/questions/`;
  for (const [path, grant] of grants) if (path.startsWith(prefix)) grant.validated = true;
}
/** Every picture of one question: the path it is asked for under, and the key its copy is kept under on the phone. */
export function pictureKeys(attempt: string, q: Question, solutions: boolean, version = "original") {
  const prefix = `/attempts/${encodeURIComponent(attempt)}/questions/`, out: { path: string; contentKey: string }[] = [];
  // A question the website supplies in cut pieces is drawn from them; its whole picture is never asked for.
  const pieces = piecesOf(q);
  for (const kind of [pieces ? "piece" : "question", ...(solutions ? ["solution"] : [])]) {
    const count = kind === "piece" ? pieces!.length : Number(kind === "question" ? q.asset_count : q.solution_asset_count) || 0;
    for (let i = 0; i < count; i++) {
      const cut = kind === "piece" ? [pieces![i].part, pieces![i].w, pieces![i].h] : [];
      out.push({ path: `${prefix}${encodeURIComponent(q.id)}/asset/${kind}/${i}${version === "original" ? "" : `?score_version=${encodeURIComponent(version)}`}`,
        contentKey: JSON.stringify([q.id, kind, i, version, count, q.asset_revision ?? q.source_revision ?? q.source_ref ?? null, ...cut]) });
    }
  }
  return out;
}
export function registerImageGrants(attempt: string, rows: Question[], solutions: boolean, version: string, invalidate: (path: string) => void, renew = false, pictureStep = 0) {
  const prefix = `/attempts/${encodeURIComponent(attempt)}/questions/`, current = new Set<string>();
  for (const q of rows) {
    const step = typeof q.asset_revision === "string" && q.asset_revision !== "" ? pictureStep : 0;
    for (const { path, contentKey } of pictureKeys(attempt, q, solutions, version)) {
      // Candidate reuse across attempts is never authorization: a fresh server
      // validator check on this newly authorized path is still mandatory.
      current.add(path);
      const old = grants.get(path);
      if (renew || old?.contentKey !== contentKey) { invalidate(path); grants.set(path, { contentKey, validated: false, step }); }
      else old.step = step; // the switch's answer arrived: the same picture, nothing on screen is loaded again
    }
  }
  for (const path of grants.keys()) if (path.startsWith(prefix) && !current.has(path)) { grants.delete(path); invalidate(path); }
}