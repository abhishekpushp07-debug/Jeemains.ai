import { storage } from "@/src/utils/storage";

// Pending answer drafts, partitioned by (user, attempt). Never shown as saved/scored.
export type Draft = { value: string; marked: boolean; revision: number; request_id: string; confidence?: number };
export type DraftMap = Record<string, Draft>;

const key = (uid: string, aid: string) => `draft.${uid}.${aid}`;
const indexKey = (uid: string) => `draft.index.${uid}`;

export async function draftIndex(uid: string): Promise<{ attempt_id: string; title: string; updated_at: number }[]> {
  const raw = await storage.getItem<string | null>(indexKey(uid), null);
  try {
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export async function loadDrafts(uid: string, aid: string): Promise<DraftMap | "corrupt"> {
  const raw = await storage.getItem<string | null>(key(uid, aid), null);
  if (!raw) return {};
  try {
    const d = JSON.parse(raw);
    if (!d || typeof d !== "object" || Array.isArray(d)) return "corrupt";
    for (const v of Object.values(d) as any[]) if (!v || typeof v.value !== "string" || typeof v.request_id !== "string" || !Number.isInteger(v.revision)) return "corrupt";
    return d;
  } catch {
    return "corrupt";
  }
}

export async function saveDrafts(uid: string, aid: string, title: string, drafts: DraftMap) {
  const empty = Object.keys(drafts).length === 0;
  const idx = (await draftIndex(uid)).filter((x) => x.attempt_id !== aid);
  if (empty) {
    await storage.removeItem(key(uid, aid));
  } else {
    await storage.setItem(key(uid, aid), JSON.stringify(drafts));
    idx.unshift({ attempt_id: aid, title, updated_at: Date.now() });
  }
  await storage.setItem(indexKey(uid), JSON.stringify(idx.slice(0, 50)));
}

export async function discardAllDrafts(uid: string) {
  for (const x of await draftIndex(uid)) await storage.removeItem(key(uid, x.attempt_id));
  await storage.removeItem(indexKey(uid));
}
