// "Meri details" for one account, the same on the phone and on jeelive.ai (owner, 28 Nov 2026: "Haan, dono jagah ek",
// and kept by the WEBSITE with the student's account: "website se kyu call nahi kr skte?"). The website's door, asked in
// memory/APP_REPLY_V5.md (part 3); the app reaches it through its usual relay with the student's own session:
//   GET /api/profile/rank-details                       -> { "rank_details": <profile> | null, "at": <ms, 0 = never> }
//   PUT /api/profile/rank-details  { "rank_details": <profile> | null, "at": <ms> }  -> the same answer
// <profile> = { at, jee: { marks, pct, rank, level, category, female, pwd, state }, comedk: { marks, rank }, bitsat: { score } }
// (the browser's rank.profile.v1 shape). null + at = emptied at that time ("Meri details hatao").
//
// The newer side wins, by `at`, except the student's own change on this phone: it always goes up (stamped just after
// the account's copy, so a phone whose clock is behind does not lose it), also when it was made without a line (it
// waits, marked, for the next look). Signed out, or before the door exists (404), everything stays on the phone exactly
// as before; a missing door is asked for again after 6 hours. Another account's details on this phone never go to an
// account, and a profile typed before signing in goes to the account only when the account has none yet.
import { api, getAssetAccount, put } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { currentProfile, profileReady, RankProfile, readProfile, stampProfile, takeProfile } from "./profile";

const DOOR = "/profile/rank-details", CLOSED = "rank.details.door", OWN = "rank.details.own", AGAIN = 6 * 3600 * 1000, GAP = 5 * 60 * 1000;
type Copy = { rank_details?: unknown; at?: number };

let lastLook = 0, flight: Promise<void> | null = null;
const changedAt = (p: RankProfile) => Math.max(p.at || 0, p.clearedAt || 0);
const plain = (p: RankProfile, at: number) => ({ at, jee: p.jee, comedk: p.comedk, bitsat: p.bitsat });

async function doorClosed() {
  return Date.now() - (Number(await storage.getItem<number>(CLOSED, 0)) || 0) < AGAIN;
}
function missing(e: any) {
  if (e?.status === 404 || e?.status === 405) void storage.setItem(CLOSED, Date.now());
}

/** On opening the Rank tab (at most every 5 minutes) and right after the student's own save or removal (`own`).
 *  Never throws. */
export function syncProfile(own = false): Promise<void> {
  if (flight) return flight.then(() => (own ? syncProfile(true) : undefined));
  if (!own && Date.now() - lastLook < GAP) return Promise.resolve();
  flight = (async () => {
    const uid = getAssetAccount();
    if (!uid) return;
    if (own) await storage.setItem(OWN, uid); // stays until the account's copy has it
    if (await doorClosed()) return;
    lastLook = Date.now();
    await profileReady();
    const got = await api<Copy>(DOOR).catch((e) => { missing(e); return null; });
    if (!got || getAssetAccount() !== uid) return;
    const local = currentProfile(), localAt = changedAt(local), remoteAt = Number(got.at) || 0;
    const remote = got.rank_details == null ? null : readProfile(got.rank_details);
    const mine = local.uid === uid, waiting = mine && (await storage.getItem<string>(OWN, "")) === uid;
    if (!waiting) {
      if (got.rank_details != null && !remote) return; // not the app's shape: nothing is changed on either side
      if (mine ? remoteAt > localAt : !!remote) return takeProfile(remote, remoteAt, uid);
      // Not this account's: another account's stays as it is; one typed before signing in goes up only to an empty copy.
      if (!mine && (local.uid || remoteAt > 0 || !local.at)) return;
      if (localAt <= remoteAt) return;
    }
    const at = Math.max(localAt, remoteAt + 1);
    const sent = await put<Copy>(DOOR, { rank_details: local.at ? plain(local, at) : null, at }).then(() => true, (e) => { missing(e); return false; });
    if (!sent || getAssetAccount() !== uid) return;
    await storage.removeItem(OWN);
    if (!mine || at !== localAt) await stampProfile(uid, at);
  })().catch(() => {}).finally(() => { flight = null; });
  return flight;
}
