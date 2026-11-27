// Who may use the phone's kept things without a line: the account whose session the server last confirmed on this
// phone, for 7 days after that confirmation (the owner's rule). Signing out, or a session the server ended, closes it.
// Kept apart from ./door.tsx so that the phone's background run (./background.ts) can read it without the screens.
import { storage } from "@/src/utils/storage";

const STAMP = "kept.confirmed.v1", DAYS = 7;
export type Who = { uid: string; name: string };

/** The account that may play from the phone without a line, or null. */
export async function offlineIdentity(): Promise<Who | null> {
  try {
    if (await storage.getItem<boolean>("jl_signed_out", false)) return null;
    const stamp = JSON.parse((await storage.getItem<string | null>(STAMP, null)) || "null");
    const age = Date.now() - Number(stamp?.at);
    // A phone whose clock was set back does not get more days out of it.
    return stamp && typeof stamp.uid === "string" && stamp.uid && age > -86400000 && age < DAYS * 86400000 ? { uid: stamp.uid, name: typeof stamp.name === "string" ? stamp.name : "" } : null;
  } catch { return null; }
}

/** The server has just confirmed this account's session on this phone (on screen, or in the background run). */
export const noteConfirmed = (who: Who) => storage.setItem(STAMP, JSON.stringify({ uid: who.uid, name: who.name || "", at: Date.now() }));
/** The server ended the session: nothing opens without a line until the next sign-in. */
export const forgetConfirmed = () => storage.removeItem(STAMP);
