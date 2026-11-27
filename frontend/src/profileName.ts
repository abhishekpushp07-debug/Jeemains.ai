// The name a student wrote for themselves: one name everywhere (Account, every leaderboard, Rapid Fire).
// The website keeps it and checks it (PUT /profile/display-name, see components/series/NameSheet.tsx) but has no way to
// read it back, so our own server notes what the website kept (backend/social.py `name_kept`) and says it here
// (GET /api/rf/name). The app never keeps a name of its own.
import { rf } from "@/src/api/client";
import { resources } from "@/src/resourceCache";
import { useCached } from "@/src/useCached";

/** The name last heard in this run of the app (and whose it is): from a save, or from the website's own leaderboard. */
export const heard: { uid?: string; name?: string } = {};
const listeners = new Set<() => void>();
/** For a part that keeps answers with the old name in them (the leaderboards): told after every save. */
export const onNameSaved = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };

/** The student's own name: "" = none yet, undefined = not known yet. */
export function useChosenName(uid?: string): string | undefined {
  const res = useCached<{ name?: string }>(uid ? `u.${uid}.rfname` : null, () => rf("/name", uid!));
  return heard.uid === uid && heard.name !== undefined ? heard.name : res.data ? res.data.name || "" : undefined;
}

/** After the website kept a name ("" = took it away): everything that shows the student's name asks again. */
export function nameSaved(uid: string, kept: string) {
  heard.uid = uid; heard.name = kept;
  resources.invalidate(`u.${uid}.rf`); // Rapid Fire's profile, player page and boards
  listeners.forEach(listener => listener());
}
