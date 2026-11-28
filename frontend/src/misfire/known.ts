// What this phone last heard from the website about which Misfire questions are "Samajh gaya" (status fixed), kept in
// the account's own store beside its kept papers (src/assets/deviceCache: signing out removes it). An Offline Misfire
// made without a line leaves these questions out (src/misfire/mock/offline.ts). It is only a memory of the website's
// answer: every Misfire list on screen still comes from the website, and the website decides what is understood.
//
// It learns from every Misfire page the website answers (src/misfire/api.ts getPage), from what the student does in
// the app (src/misfire/store.ts patchMisfire), and from a quiet check while signed in (offline.ts refreshKnown).
import { getAssetAccount, onAssetScopeReset } from "@/src/api/client";
import { readKeptText, saveKeptText } from "@/src/assets/deviceCache/cache";

const DOC = "mf.fixed";
type Doc = { v: 1; ids: string[]; checked: number };

let owner: string | null = null, ids: Set<string> | null = null, checked = 0, version = 0;
let loading: Promise<Set<string>> | null = null, timer: ReturnType<typeof setTimeout> | null = null;
onAssetScopeReset(() => { owner = null; ids = null; checked = 0; loading = null; version++; if (timer) { clearTimeout(timer); timer = null; } });

/** Goes up whenever what is known changes (a question in, a question out, a whole new list), not only its size. */
export const knownVersion = () => version;

/** The Misfire ids (`<attempt id>:<question id>`) last known as "Samajh gaya" for the account whose store is open. */
export function knownFixed(): Promise<Set<string>> {
  const uid = getAssetAccount();
  if (!uid) return Promise.resolve(new Set());
  if (ids && owner === uid) return Promise.resolve(ids);
  if (loading && owner === uid) return loading;
  owner = uid;
  loading = (async () => {
    let doc: Doc | null = null;
    try { doc = JSON.parse((await readKeptText(DOC)) || "null"); } catch { /* unreadable: learnt again */ }
    const got = new Set<string>(doc?.v === 1 && Array.isArray(doc.ids) ? doc.ids.filter((x) => typeof x === "string") : []);
    if (getAssetAccount() === uid && owner === uid) { ids = got; checked = Number(doc?.checked) || 0; version++; }
    return got;
  })().finally(() => { loading = null; });
  return loading;
}

/** When the whole list was last read from the website (0: never). */
export const knownChecked = () => checked;

function save(uid: string) {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    timer = null;
    if (getAssetAccount() === uid && owner === uid && ids) void saveKeptText(DOC, JSON.stringify({ v: 1, ids: [...ids], checked }));
  }, 800);
}

/** Questions the website (or the student, a moment ago) just showed with their status: "fixed" is remembered, "open" forgotten. */
export function noteStatus(items: { id?: string; status?: string }[]) {
  const uid = getAssetAccount();
  if (!uid || !items?.length) return;
  void knownFixed().then((set) => {
    if (getAssetAccount() !== uid) return;
    let changed = false;
    for (const it of items) {
      if (!it?.id) continue;
      if (it.status === "fixed" && !set.has(it.id)) { set.add(it.id); changed = true; } else if (it.status === "open" && set.delete(it.id)) changed = true;
    }
    if (changed) { version++; save(uid); }
  }).catch(() => {});
}

/** The website's whole "Samajh gaya" list was just read: `complete` = every page of it (then it replaces what was known). */
export async function replaceKnown(next: string[], complete: boolean) {
  const uid = getAssetAccount();
  if (!uid) return;
  const set = await knownFixed();
  if (getAssetAccount() !== uid) return;
  if (complete) set.clear();
  next.forEach((id) => set.add(id));
  checked = Date.now();
  version++;
  save(uid);
}
