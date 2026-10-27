type Question = { id: string; asset_count?: number; solution_asset_count?: number; asset_revision?: unknown; source_revision?: unknown; source_ref?: unknown };
export type ImageGrant = { contentKey: string; validated: boolean };
const grants = new Map<string, ImageGrant>();
export const imageGrant = (path: string) => grants.get(path);
export const clearImageGrants = () => grants.clear();
export function registerImageGrants(attempt: string, rows: Question[], solutions: boolean, version: string, invalidate: (path: string) => void, renew = false) {
  const prefix = `/attempts/${encodeURIComponent(attempt)}/questions/`, current = new Set<string>();
  for (const q of rows) for (const kind of solutions ? ["question", "solution"] : ["question"]) {
    const count = Number(kind === "question" ? q.asset_count : q.solution_asset_count) || 0;
    for (let i = 0; i < count; i++) {
      const path = `${prefix}${encodeURIComponent(q.id)}/asset/${kind}/${i}${version === "original" ? "" : `?score_version=${encodeURIComponent(version)}`}`;
      // Candidate reuse across attempts is never authorization: a fresh server
      // validator check on this newly authorized path is still mandatory.
      const contentKey = JSON.stringify([q.id, kind, i, version, count, q.asset_revision ?? q.source_revision ?? q.source_ref ?? null]);
      current.add(path);
      if (renew || grants.get(path)?.contentKey !== contentKey) { invalidate(path); grants.set(path, { contentKey, validated: false }); }
    }
  }
  for (const path of grants.keys()) if (path.startsWith(prefix) && !current.has(path)) { grants.delete(path); invalidate(path); }
}